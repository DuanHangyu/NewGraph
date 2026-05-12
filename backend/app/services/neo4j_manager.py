"""
Neo4j 连接管理
使用单例模式管理 Neo4j Driver
"""

import logging
from typing import Optional
from neo4j import GraphDatabase

from ..config import Config

logger = logging.getLogger(__name__)


class Neo4jManager:
    """Neo4j 连接管理器（单例模式）"""

    _instance: Optional['Neo4jManager'] = None
    _driver: Optional[GraphDatabase.driver] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_driver(cls) -> GraphDatabase.driver:
        """
        获取 Neo4j Driver 实例

        Returns:
            Neo4j Driver

        Raises:
            ValueError: 如果连接配置无效
        """
        if cls._driver is None:
            cls._initialize_driver()
        return cls._driver

    @classmethod
    def _initialize_driver(cls):
        """初始化 Neo4j Driver"""
        if not Config.NEO4J_URI or not Config.NEO4J_USER or not Config.NEO4J_PASSWORD:
            raise ValueError("Neo4j 配置不完整，请检查 NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")

        try:
            cls._driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD),
                max_connection_lifetime=300,
                max_connection_pool_size=5,
                connection_acquisition_timeout=120,
                connection_timeout=30,
                max_transaction_retry_time=60,
                resolver=None
            )
            logger.info(f"Neo4j Driver 初始化成功: {Config.NEO4J_URI}")

            # 验证连接
            cls._driver.verify_connectivity()
            logger.info("Neo4j 连接验证成功")

        except Exception as e:
            logger.error(f"Neo4j Driver 初始化失败: {e}")
            cls._driver = None
            raise

    @classmethod
    def close(cls):
        """关闭 Neo4j 连接"""
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
            logger.info("Neo4j Driver 已关闭")

    @classmethod
    def get_session(cls):
        """
        获取 Neo4j Session

        Returns:
            Neo4j Session
        """
        driver = cls.get_driver()
        return driver.session()

    @classmethod
    def execute_query(cls, query: str, parameters: dict = None, database: str = "neo4j"):
        """
        执行 Cypher 查询

        Args:
            query: Cypher 查询语句
            parameters: 查询参数
            database: 数据库名称（默认 neo4j）

        Returns:
            查询结果列表
        """
        with cls.get_driver().session(database=database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]


def get_neo4j_driver():
    """便捷函数：获取 Neo4j Driver"""
    return Neo4jManager.get_driver()


def get_neo4j_session():
    """便捷函数：获取 Neo4j Session"""
    return Neo4jManager.get_session()
