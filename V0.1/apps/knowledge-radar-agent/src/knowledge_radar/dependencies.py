"""
Knowledge Radar Agent 依赖注入

提供 FastAPI 依赖项，包括：
- get_settings: 获取应用配置
- get_db_session: 获取数据库会话
- get_agent_graph: 获取 Agent 图
- get_services: 获取服务实例
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from knowledge_radar.config import get_settings, Settings
from knowledge_radar.logging_config import get_logger

logger = get_logger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# 全局引擎和会话工厂（延迟初始化）
_engine = None
_async_session_factory = None


def get_engine():
    """获取或创建数据库引擎"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.database.DATABASE_POOL_SIZE,
            max_overflow=settings.database.DATABASE_MAX_OVERFLOW,
            echo=False,
        )
    return _engine


def get_session_factory():
    """获取或创建会话工厂"""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖项
    
    用法:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# Agent Graph 依赖（TODO: 后续实现）
# =============================================================================

_agent_graph = None


def get_agent_graph():
    """
    获取 Agent Graph 实例
    
    TODO_FEISHU_DOC_LOOKUP:
    需要确认 LangGraph StateGraph 的具体实现方式
    需要确认知识雷达各场景的具体节点定义
    """
    global _agent_graph
    if _agent_graph is None:
        # TODO: 后续实现
        # from knowledge_radar.graph import build_agent_graph
        # _agent_graph = build_agent_graph()
        _agent_graph = _PlaceholderAgentGraph()
    return _agent_graph


class _PlaceholderAgentGraph:
    """临时占位符，后续替换为真实实现"""
    
    async def ainvoke(self, input_data: dict, config: Optional[dict] = None):
        """运行 Agent Graph"""
        logger.warning("Using placeholder agent graph - implement actual graph")
        return {
            "success": True,
            "execution_id": f"exec_placeholder_{id(input_data)}",
            "summary": "Placeholder response - implement actual agent graph",
            "source_refs": [],
        }


# =============================================================================
# 服务层依赖（TODO: 后续实现）
# =============================================================================

class Services:
    """
    服务容器
    
    TODO_FEISHU_DOC_LOOKUP:
    需要确认飞书 SDK 的具体服务接口
    需要确认各服务的初始化参数
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._feishu_client = None
        self._llm_client = None
        self._embedding_client = None
        self._redis_client = None
    
    @property
    def feishu_client(self):
        """飞书客户端"""
        # TODO_FEISHU_DOC_LOOKUP: 使用 lark-oapi 或 lark-cli SDK
        # 需要确认具体的客户端初始化方式
        if self._feishu_client is None:
            # from lark_oapi import ...
            # self._feishu_client = ...
            self._feishu_client = _PlaceholderFeishuClient()
        return self._feishu_client
    
    @property
    def llm_client(self):
        """LLM 客户端"""
        if self._llm_client is None:
            # TODO: 使用 httpx 调用 LLM API
            self._llm_client = _PlaceholderLLMClient()
        return self._llm_client
    
    @property
    def embedding_client(self):
        """Embedding 客户端"""
        if self._embedding_client is None:
            # TODO: 使用 httpx 调用 Embedding API
            self._embedding_client = _PlaceholderEmbeddingClient()
        return self._embedding_client
    
    @property
    def redis_client(self):
        """Redis 客户端"""
        # TODO: 使用 redis-py
        if self._redis_client is None:
            self._redis_client = _PlaceholderRedisClient()
        return self._redis_client


class _PlaceholderFeishuClient:
    """飞书客户端占位符"""
    pass


class _PlaceholderLLMClient:
    """LLM客户端占位符"""
    pass


class _PlaceholderEmbeddingClient:
    """Embedding客户端占位符"""
    pass


class _PlaceholderRedisClient:
    """Redis客户端占位符"""
    pass


_services: Optional[Services] = None


def get_services() -> Services:
    """获取服务容器单例"""
    global _services
    if _services is None:
        settings = get_settings()
        _services = Services(settings)
    return _services


# =============================================================================
# 依赖项入口
# =============================================================================

def get_db():
    """
    数据库会话依赖项的快捷方式
    
    避免循环导入问题
    """
    return get_db_session()
