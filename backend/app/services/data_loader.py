"""
中文文本分块 + 数据集导入服务
"""

import os
import re
import logging
from datetime import datetime, timezone
from typing import Any

from ..utils.async_bridge import AsyncBridge
from .graphiti_service import GraphitiService

logger = logging.getLogger(__name__)

# 中文标题/章节分割模式
SECTION_PATTERNS = [
    re.compile(r'^#{1,4}\s+.+', re.MULTILINE),          # Markdown 标题
    re.compile(r'^第[一二三四五六七八九十百千\d]+[章节篇部].+', re.MULTILINE),  # 第X章/节
    re.compile(r'^[一二三四五六七八九十]+[、．.].+', re.MULTILINE),           # 一、二、三、
    re.compile(r'^\d+[、．.]\s*.+', re.MULTILINE),                        # 1、2、3、
    re.compile(r'^\d+\.\d*\s+.+', re.MULTILINE),                         # 1.1 标题
]


def chunk_chinese_text(text: str, max_chars: int = 3000) -> list[dict[str, str]]:
    """
    按中文标题/章节分割文本为 chunks。

    Args:
        text: 原始文本
        max_chars: 每个 chunk 的最大字符数

    Returns:
        [{name: "章节标题", episode_body: "章节内容"}, ...]
    """
    # 尝试按标题模式分割
    split_positions = []
    for pattern in SECTION_PATTERNS:
        for m in pattern.finditer(text):
            split_positions.append(m.start())

    if not split_positions:
        # 没有找到标题模式，按段落分割
        return _chunk_by_paragraph(text, max_chars)

    # 去重排序
    split_positions = sorted(set(split_positions))

    # 确保包含起始位置
    if split_positions[0] != 0:
        split_positions.insert(0, 0)

    chunks = []
    for i in range(len(split_positions)):
        start = split_positions[i]
        end = split_positions[i + 1] if i + 1 < len(split_positions) else len(text)
        section_text = text[start:end].strip()

        if not section_text:
            continue

        # 提取标题（第一行）
        first_line = section_text.split('\n', 1)[0].strip()
        # 清理标题中的 Markdown 标记
        title = re.sub(r'^#+\s*', '', first_line)
        title = title[:100] if title else f"段落 {i + 1}"

        # 如果 chunk 过大，进一步分割
        if len(section_text) > max_chars:
            sub_chunks = _split_long_section(title, section_text, max_chars)
            chunks.extend(sub_chunks)
        else:
            chunks.append({
                "name": title,
                "episode_body": section_text,
            })

    return chunks


def _chunk_by_paragraph(text: str, max_chars: int) -> list[dict[str, str]]:
    """按段落分割文本"""
    paragraphs = re.split(r'\n{2,}', text)
    chunks = []
    current_text = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_text) + len(para) + 2 > max_chars:
            if current_text:
                first_line = current_text.split('\n', 1)[0][:50]
                chunks.append({
                    "name": first_line,
                    "episode_body": current_text.strip(),
                })
            current_text = para
        else:
            current_text += "\n\n" + para if current_text else para

    if current_text.strip():
        first_line = current_text.split('\n', 1)[0][:50]
        chunks.append({
            "name": first_line,
            "episode_body": current_text.strip(),
        })

    return chunks


def _split_long_section(title: str, text: str, max_chars: int) -> list[dict[str, str]]:
    """分割过长的章节"""
    chunks = []
    # 按段落分割
    paragraphs = text.split('\n')
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 1 > max_chars:
            if current:
                chunks.append({
                    "name": f"{title}（{len(chunks) + 1}）",
                    "episode_body": current.strip(),
                })
            current = para
        else:
            current += "\n" + para if current else para

    if current.strip():
        chunks.append({
            "name": f"{title}（{len(chunks) + 1}）",
            "episode_body": current.strip(),
        })

    return chunks


def ingest_dataset(dataset_dir: str, group_id: str, progress_callback=None) -> dict[str, Any]:
    """
    将数据集目录下的 .md 文件导入 Graphiti

    Args:
        dataset_dir: 数据集目录路径
        group_id: Graphiti group_id（用于隔离）
        progress_callback: 进度回调 fn(completed, total)

    Returns:
        {document_count, episode_count, status}
    """
    if not os.path.exists(dataset_dir):
        raise FileNotFoundError(f"数据集目录不存在: {dataset_dir}")

    # 收集所有 .md 文件
    md_files = sorted([
        f for f in os.listdir(dataset_dir)
        if f.endswith(('.md', '.txt', '.markdown'))
    ])

    if not md_files:
        raise ValueError(f"数据集目录中没有文件: {dataset_dir}")

    all_episodes = []
    for filename in md_files:
        filepath = os.path.join(dataset_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        chunks = chunk_chinese_text(text)

        for chunk in chunks:
            all_episodes.append({
                "name": f"{filename}::{chunk['name']}",
                "episode_body": chunk["episode_body"],
                "source_description": f"dataset:{os.path.basename(dataset_dir)}",
                "reference_id": filename,
                "reference_time": datetime.now(timezone.utc),
            })

    logger.info(f"准备导入 {len(md_files)} 个文档, {len(all_episodes)} 个 episodes")

    # 确保 Graphiti 索引已创建
    AsyncBridge.run(GraphitiService.ensure_indices())

    # 并发批量导入
    result = AsyncBridge.run(
        GraphitiService.ingest_episodes(
            all_episodes, group_id=group_id, progress_callback=progress_callback
        )
    )

    return {
        "document_count": len(md_files),
        "episode_count": result.get("episode_count", len(all_episodes)),
        "status": result.get("status", "ok"),
    }
