"""
Feedback Schema - 反馈定义

定义用户对推送内容的反馈
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field


FeedbackType = Literal[
    "clicked",        # 点击查看
    "helpful",        # 有帮助
    "not_helpful",    # 无帮助
    "hide_topic",     # 隐藏话题
    "follow_up",      # 想要跟进
    "ignored",        # 忽略
]


class FeedbackEvent(BaseModel):
    """
    反馈事件
    
    记录用户对推送内容的反馈
    """
    feedback_id: str = Field(description="反馈唯一ID")
    push_id: str = Field(description="关联的推送ID")
    execution_id: str = Field(description="关联的执行ID")
    
    # 用户信息
    user_id: str = Field(description="用户ID")
    
    # 反馈内容
    feedback_type: FeedbackType = Field(description="反馈类型")
    content: str = Field(
        default="",
        description="反馈详细文本"
    )
    
    # 关联的知识
    knowledge_id: Optional[str] = Field(
        default=None,
        description="反馈关联的知识ID"
    )
    
    # 行为数据
    click_duration_ms: Optional[int] = Field(
        default=None,
        description="点击停留时长（毫秒）"
    )
    interaction_type: Optional[str] = Field(
        default=None,
        description="交互类型"
    )
    
    # 元数据
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外元数据"
    )
    
    # 时间戳
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="反馈时间"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "feedback_id": "fb_123456",
                    "push_id": "push_789",
                    "execution_id": "exec_001",
                    "user_id": "user_001",
                    "feedback_type": "helpful",
                    "content": "这个决策总结很有帮助",
                    "knowledge_id": "ki_123",
                    "click_duration_ms": 5000
                }
            ]
        }
    }
