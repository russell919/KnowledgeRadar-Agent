"""
Knowledge Radar Schemas

Pydantic 模型定义，用于 API 请求/响应、数据验证、状态管理
"""

from knowledge_radar.schemas.trigger import (
    TriggerType,
    Trigger,
)
from knowledge_radar.schemas.source import (
    SourceType,
    SourceObject,
    SourceRef,
)
from knowledge_radar.schemas.knowledge import (
    KnowledgeType,
    KnowledgeItem,
    KnowledgeChunk,
)
from knowledge_radar.schemas.scene import (
    SceneContext,
    SceneType,
)
from knowledge_radar.schemas.retrieval import (
    RetrievalQuery,
    RetrievalHit,
    RetrievalResult,
)
from knowledge_radar.schemas.push import (
    RecipientScore,
    ContentScore,
    PushDecision,
    RankingResult,
)
from knowledge_radar.schemas.profile import (
    UserProfile,
)
from knowledge_radar.schemas.feedback import (
    FeedbackType,
    FeedbackEvent,
)
from knowledge_radar.schemas.cards import (
    CardSection,
    CardAction,
    OutputCard,
    FeishuCardPayload,
)
from knowledge_radar.schemas.state import (
    KnowledgeRadarState,
)

__all__ = [
    # Trigger
    "TriggerType",
    "Trigger",
    # Source
    "SourceType",
    "SourceObject",
    "SourceRef",
    # Knowledge
    "KnowledgeType",
    "KnowledgeItem",
    "KnowledgeChunk",
    # Scene
    "SceneContext",
    "SceneType",
    # Retrieval
    "RetrievalQuery",
    "RetrievalHit",
    "RetrievalResult",
    # Push
    "RecipientScore",
    "ContentScore",
    "PushDecision",
    "RankingResult",
    # Profile
    "UserProfile",
    # Feedback
    "FeedbackType",
    "FeedbackEvent",
    # Cards
    "CardSection",
    "CardAction",
    "OutputCard",
    "FeishuCardPayload",
    # State
    "KnowledgeRadarState",
]
