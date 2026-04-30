"""
Knowledge Radar Agent 配置管理

使用 pydantic-settings 进行配置管理，支持环境变量注入
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_radar",
        description="PostgreSQL数据库连接URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)


class RedisSettings(BaseSettings):
    """Redis配置"""
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, ge=1)


class CelerySettings(BaseSettings):
    """Celery配置"""
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2")


class OpenClawSettings(BaseSettings):
    """OpenClaw配置"""
    OPENCLAW_GATEWAY_URL: str = Field(default="http://localhost:18789")
    OPENCLAW_API_KEY: Optional[str] = Field(default=None)
    OPENCLAW_WS_URL: str = Field(default="ws://localhost:18789/ws")


class FeishuSettings(BaseSettings):
    """飞书配置"""
    FEISHU_APP_ID: Optional[str] = Field(default=None)
    FEISHU_APP_SECRET: Optional[str] = Field(default=None)
    FEISHU_VERIFICATION_TOKEN: Optional[str] = Field(default=None)
    FEISHU_ENCRYPT_KEY: Optional[str] = Field(default=None)


class LLMSettings(BaseSettings):
    """LLM配置"""
    LLM_BASE_URL: str = Field(default="https://ark.cn-beijing.volces.com/api/v3")
    LLM_API_KEY: Optional[str] = Field(default=None)
    LLM_MODEL: str = Field(default="doubao-2.0-pro-32k")


class EmbeddingSettings(BaseSettings):
    """Embedding配置"""
    EMBEDDING_MODEL: str = Field(default="text-embedding-v03")
    EMBEDDING_DIMENSION: int = Field(default=1536)
    RERANK_MODEL: str = Field(default="bge-reranker-v2-m3")


class AgentSettings(BaseSettings):
    """Agent行为配置"""
    ENABLE_HUMAN_PREVIEW: bool = Field(default=True)
    DEFAULT_PUSH_DRY_RUN: bool = Field(default=False)
    MAX_RECEIVERS_PER_PUSH: int = Field(default=100)
    PUSH_BATCH_SIZE: int = Field(default=20)


class ServiceSettings(BaseSettings):
    """服务配置"""
    SERVICE_HOST: str = Field(default="0.0.0.0")
    SERVICE_PORT: int = Field(default=8787, ge=1, le=65535)
    LOG_LEVEL: str = Field(default="INFO")
    WORKERS: int = Field(default=4, ge=1)

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()


class Settings(BaseSettings):
    """
    Knowledge Radar Agent 全局配置
    
    从环境变量加载配置，支持 .env 文件
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # 子配置组
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    openclaw: OpenClawSettings = Field(default_factory=OpenClawSettings)
    feishu: FeishuSettings = Field(default_factory=FeishuSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    service: ServiceSettings = Field(default_factory=ServiceSettings)
    
    # 直接暴露的字段（兼容性）
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_radar")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    @field_validator("DATABASE_URL", "REDIS_URL", mode="before")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        return v


@lru_cache
def get_settings() -> Settings:
    """
    获取全局配置单例
    
    使用 lru_cache 确保配置只加载一次
    """
    return Settings()
