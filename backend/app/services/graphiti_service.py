"""
Graphiti 客户端封装

封装 Graphiti SDK，提供：
- 懒初始化的 Graphiti 客户端
- AI 领域实体类型定义
- 搜索接口
"""

import os
import asyncio
import time
import logging
from typing import Any

from pydantic import BaseModel, Field

from ..config import Config

logger = logging.getLogger(__name__)


# ============== DashScope 兼容 Embedder ==============

DASHSCOPE_EMBED_BATCH_SIZE = 10


def create_dashscope_embedder(config):
    """创建 DashScope 兼容的 embedder，通过子类覆盖 create_batch 限制批量大小"""
    from graphiti_core.embedder.openai import OpenAIEmbedder

    class _BatchLimitedEmbedder(OpenAIEmbedder):
        async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
            results: list[list[float]] = []
            for i in range(0, len(input_data_list), DASHSCOPE_EMBED_BATCH_SIZE):
                batch = input_data_list[i:i + DASHSCOPE_EMBED_BATCH_SIZE]
                batch_results = await super().create_batch(batch)
                results.extend(batch_results)
            return results

    return _BatchLimitedEmbedder(config=config)

# ============== AI 领域实体类型定义 ==============


class Technology(BaseModel):
    """技术实体 — 算法、框架、工具、平台等"""
    category: str | None = Field(default=None, description="类别：算法/框架/工具/平台/硬件")
    domain: str | None = Field(default=None, description="所属领域")
    maturity: str | None = Field(default=None, description="成熟度：研究/应用/成熟")


class Researcher(BaseModel):
    """研究人员实体"""
    affiliation: str | None = Field(default=None, description="所属机构")
    field: str | None = Field(default=None, description="研究方向")
    contribution: str | None = Field(default=None, description="主要贡献")


class Organization(BaseModel):
    """组织机构实体 — 公司、高校、研究所等"""
    org_type: str | None = Field(default=None, description="类型：企业/高校/研究所/政府")
    location: str | None = Field(default=None, description="所在地")
    focus_area: str | None = Field(default=None, description="主要领域")


class Concept(BaseModel):
    """概念实体 — 理论、方法、原理等"""
    concept_description: str | None = Field(default=None, description="概念描述")
    field: str | None = Field(default=None, description="所属领域")


class Application(BaseModel):
    """应用场景实体"""
    industry: str | None = Field(default=None, description="所属行业")
    app_description: str | None = Field(default=None, description="应用描述")


# 实体类型注册表（Graphiti 要求 dict[str, type[BaseModel]] 格式）
AI_ENTITY_TYPES = {
    "Technology": Technology,
    "Researcher": Researcher,
    "Organization": Organization,
    "Concept": Concept,
    "Application": Application,
}


class GraphitiService:
    """Graphiti 客户端服务（单例模式）"""

    _client = None
    _initialized: bool = False

    @classmethod
    async def get_client(cls):
        """获取或初始化 Graphiti 客户端"""
        if cls._client is not None:
            return cls._client

        # 设置 OPENAI_API_KEY 环境变量（Graphiti 内部的 embedder/reranker 会读取）
        os.environ['OPENAI_API_KEY'] = Config.LLM_API_KEY or ''
        if Config.LLM_BASE_URL:
            os.environ['OPENAI_BASE_URL'] = Config.LLM_BASE_URL

        # 配置 LLM 客户端（使用 OpenAIGenericClient 兼容 DashScope 等非 OpenAI 提供商）
        from graphiti_core import Graphiti
        from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
        from graphiti_core.llm_client.config import LLMConfig
        from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig

        model_name = Config.LLM_MODEL_NAME or 'qwen-plus'
        llm_config = LLMConfig(
            api_key=Config.LLM_API_KEY,
            model=model_name,
            small_model=model_name,
            base_url=Config.LLM_BASE_URL,
        )
        llm_client = OpenAIGenericClient(config=llm_config)

        # 配置 embedder 使用 DashScope 的 embedding 模型
        embedder_config = OpenAIEmbedderConfig(
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL,
            embedding_model='text-embedding-v3',
            embedding_dim=1024,
        )
        embedder = create_dashscope_embedder(embedder_config)

        # 配置 Neo4j 驱动（AuraDB 数据库名可能不是默认的 neo4j）
        from graphiti_core.driver.neo4j_driver import Neo4jDriver

        database = Config.NEO4J_USER  # AuraDB 数据库名通常等于用户名
        graph_driver = Neo4jDriver(
            uri=Config.NEO4J_URI,
            user=Config.NEO4J_USER,
            password=Config.NEO4J_PASSWORD,
            database=database,
        )

        cls._client = Graphiti(
            uri=Config.NEO4J_URI,
            user=Config.NEO4J_USER,
            password=Config.NEO4J_PASSWORD,
            llm_client=llm_client,
            embedder=embedder,
            graph_driver=graph_driver,
        )

        logger.info(f"Graphiti 客户端初始化成功 (model={model_name})")
        return cls._client

    @classmethod
    async def ensure_indices(cls):
        """确保 Neo4j 索引和约束已创建（幂等操作）"""
        client = await cls.get_client()
        await client.build_indices_and_constraints()
        cls._initialized = True
        logger.info("Graphiti 索引和约束已创建")

    @classmethod
    async def ingest_episodes(
        cls,
        episodes: list[dict],
        group_id: str | None = None,
        max_concurrency: int = 5,
        progress_callback=None,
    ) -> dict[str, Any]:
        """
        并发批量导入 episodes 到 Graphiti

        Args:
            episodes: [{name, episode_body, source_description, reference_id?, reference_time?}]
            group_id: Graphiti group_id（用于隔离不同项目的图谱）
            max_concurrency: 最大并发数（避免压垮 LLM API）
            progress_callback: 进度回调 fn(completed, total)

        Returns:
            {episode_count, status}
        """
        client = await cls.get_client()

        if not cls._initialized:
            await cls.ensure_indices()

        from datetime import datetime, timezone
        from graphiti_core.nodes import EpisodeType

        semaphore = asyncio.Semaphore(max_concurrency)
        completed = [0]  # mutable counter for closure
        total = len(episodes)
        results = []
        errors = []

        async def _process_episode(idx: int, ep: dict):
            async with semaphore:
                t0 = time.monotonic()
                try:
                    result = await client.add_episode(
                        name=ep.get('name', 'untitled'),
                        episode_body=ep['episode_body'],
                        source_description=ep.get('source_description', 'dataset'),
                        source=EpisodeType.text,
                        reference_time=ep.get('reference_time') or datetime.now(timezone.utc),
                        group_id=group_id,
                        entity_types=AI_ENTITY_TYPES,
                    )
                    elapsed = time.monotonic() - t0
                    completed[0] += 1
                    logger.info(
                        f"Episode {completed[0]}/{total} 完成 ({elapsed:.1f}s): {ep.get('name', '?')[:40]}"
                    )
                    if progress_callback:
                        progress_callback(completed[0], total)
                    return result
                except Exception as e:
                    elapsed = time.monotonic() - t0
                    completed[0] += 1
                    logger.error(
                        f"Episode {completed[0]}/{total} 失败 ({elapsed:.1f}s): {ep.get('name', '?')[:40]} - {e}"
                    )
                    errors.append({"episode": ep.get('name', '?'), "error": str(e)})
                    return None

        logger.info(f"开始并发导入 {total} 个 episodes (并发={max_concurrency})")
        t_start = time.monotonic()

        tasks = [_process_episode(i, ep) for i, ep in enumerate(episodes)]
        raw_results = await asyncio.gather(*tasks)

        elapsed_total = time.monotonic() - t_start
        results = [r for r in raw_results if r is not None]

        logger.info(
            f"Graphiti 并发导入完成: {len(results)}/{total} 成功, "
            f"{len(errors)} 失败, 总耗时 {elapsed_total:.1f}s"
        )
        return {
            "episode_count": len(results),
            "total": total,
            "errors": len(errors),
            "status": "ok" if not errors else "partial",
        }

    @classmethod
    async def search(cls, query: str, group_id: str | None = None, num_results: int = 20) -> list[dict[str, Any]]:
        """
        搜索相关边（包含实体关系）

        Args:
            query: 查询文本
            group_id: Graphiti group_id
            num_results: 返回结果数量

        Returns:
            搜索结果列表（边 + 源/目标节点信息）
        """
        client = await cls.get_client()

        group_ids = [group_id] if group_id else None

        results = await client.search(
            query=query,
            group_ids=group_ids,
            num_results=num_results,
        )

        # 收集所有唯一的 source/target node UUID
        node_uuids = set()
        for edge in results:
            src = getattr(edge, 'source_node_uuid', None)
            tgt = getattr(edge, 'target_node_uuid', None)
            if src:
                node_uuids.add(src)
            if tgt:
                node_uuids.add(tgt)

        # 批量查询节点信息
        node_map = {}
        if node_uuids:
            from graphiti_core.nodes import EntityNode
            nodes = await EntityNode.get_by_uuids(client.driver, list(node_uuids))
            for node in nodes:
                node_map[node.uuid] = {
                    "uuid": node.uuid,
                    "name": getattr(node, 'name', ''),
                    "summary": getattr(node, 'summary', ''),
                    "labels": list(getattr(node, 'labels', [])),
                }

        # 将 EntityEdge 结果转为可序列化的字典
        serialized = []
        for edge in results:
            src_uuid = getattr(edge, 'source_node_uuid', '')
            tgt_uuid = getattr(edge, 'target_node_uuid', '')

            serialized.append({
                "uuid": getattr(edge, 'uuid', ''),
                "name": getattr(edge, 'name', '') or getattr(edge, 'fact', ''),
                "fact": getattr(edge, 'fact', ''),
                "source_node": node_map.get(src_uuid, {"uuid": src_uuid, "name": ""}),
                "target_node": node_map.get(tgt_uuid, {"uuid": tgt_uuid, "name": ""}),
            })

        return serialized

    @classmethod
    async def close(cls):
        """关闭 Graphiti 客户端"""
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
            cls._initialized = False
            logger.info("Graphiti 客户端已关闭")
