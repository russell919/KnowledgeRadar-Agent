"""
Knowledge Radar Integrations

外部服务集成层 - 封装与外部服务的通信
"""

from knowledge_radar.integrations.openclaw_client import OpenClawClient
from knowledge_radar.integrations.feishu_client import (
    FeishuClient,
    MockFeishuClient,
    OpenClawFeishuClient,
    FeishuCLIClient,
)
from knowledge_radar.integrations.llm_client import LLMClient
from knowledge_radar.integrations.embedding_client import EmbeddingClient
from knowledge_radar.integrations.rerank_client import RerankClient

__all__ = [
    # OpenClaw
    "OpenClawClient",
    # Feishu
    "FeishuClient",
    "MockFeishuClient",
    "OpenClawFeishuClient",
    "FeishuCLIClient",
    # LLM
    "LLMClient",
    # Embedding
    "EmbeddingClient",
    # Rerank
    "RerankClient",
]
