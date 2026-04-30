"""
Database Configuration and Session Management

使用 SQLAlchemy 2.0 async 风格
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from knowledge_radar.config import get_settings

# 创建 declarative Base
Base = declarative_base()

# 全局引擎和会话工厂（延迟初始化）
_engine = None
_async_session_factory = None


def get_engine():
    """
    获取或创建数据库引擎
    
    使用单例模式确保只有一个引擎实例
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.database.DATABASE_POOL_SIZE,
            max_overflow=settings.database.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
            echo=settings.service.LOG_LEVEL == "DEBUG",
        )
    return _engine


def get_session_factory():
    """
    获取或创建会话工厂
    
    使用单例模式确保只有一个会话工厂实例
    """
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
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


async def init_db():
    """
    初始化数据库
    
    创建所有表（仅用于开发环境）
    生产环境应使用 Alembic 迁移
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    关闭数据库连接
    
    应用关闭时调用
    """
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
