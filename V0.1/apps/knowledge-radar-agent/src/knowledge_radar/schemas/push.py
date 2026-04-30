"""
Push Schema - 推送决策定义

定义知识推送的接收者选择和内容排序
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from knowledge_radar.schemas.knowledge import KnowledgeItem


class RecipientScore(BaseModel):
    """
    接收者评分
    
    评估用户对某条知识的需要程度
    """
    user_id: str = Field(description="用户ID")
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="推送评分"
    )
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="分数分解"
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="推荐原因"
    )
    should_push: bool = Field(
        default=True,
        description="是否应该推送"
    )
    push_channel: str = Field(
        default="feishu_im",
        description="推送渠道"
    )


class ContentScore(BaseModel):
    """
    内容评分
    
    评估某条知识对特定用户的重要性
    """
    knowledge_id: str = Field(description="知识ID")
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="相关性评分"
    )
    authority_score: float = Field(
        ge=0.0,
        le=1.0,
        description="权威性评分"
    )
    freshness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="新鲜度评分"
    )
    combined_score: float = Field(
        ge=0.0,
        le=1.0,
        description="综合评分"
    )


class PushDecision(BaseModel):
    """
    推送决策
    
    决定向某用户推送某条知识
    """
    user_id: str = Field(description="用户ID")
    knowledge_id: str = Field(description="知识ID")
    decision: str = Field(
        description="决策结果: push, skip, defer"
    )
    reason: str = Field(description="决策原因")
    priority: str = Field(
        default="normal",
        description="优先级: low, normal, high"
    )
    defer_until: Optional[datetime] = Field(
        default=None,
        description="推迟推送时间"
    )
    dry_run: bool = Field(
        default=False,
        description="是否为预览模式"
    )


class RankingResult(BaseModel):
    """
    排序结果
    
    完整的推送排序结果
    """
    push_id: str = Field(description="推送事件ID")
    execution_id: str = Field(description="执行ID")
    
    # 接收者决策
    recipient_decisions: List[PushDecision] = Field(
        default_factory=list,
        description="各接收者的推送决策"
    )
    
    # 统计数据
    total_recipients: int = Field(description="总接收人数")
    push_count: int = Field(description="实际推送数")
    skip_count: int = Field(description="跳过数")
    defer_count: int = Field(description="推迟数")
    
    # 推送内容摘要
    content_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="推送内容摘要"
    )
    
    # 元数据
    dry_run: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "push_id": "push_123456",
                    "execution_id": "exec_789",
                    "recipient_decisions": [
                        {
                            "user_id": "user_001",
                            "knowledge_id": "ki_123",
                            "decision": "push",
                            "reason": "用户参与了该项目相关讨论",
                            "priority": "normal"
                        }
                    ],
                    "total_recipients": 1,
                    "push_count": 1,
                    "skip_count": 0,
                    "defer_count": 0
                }
            ]
        }
    }
