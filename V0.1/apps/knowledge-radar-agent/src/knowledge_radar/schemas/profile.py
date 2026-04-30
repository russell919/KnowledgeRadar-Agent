"""
Profile Schema - 用户画像定义

定义用户画像数据结构
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """
    用户画像
    
    描述用户的信息、兴趣和偏好
    """
    user_id: str = Field(description="用户唯一ID")
    
    # 标签体系
    role_tags: List[str] = Field(
        default_factory=list,
        description="角色标签，如: PM, Engineer, Designer"
    )
    project_tags: List[str] = Field(
        default_factory=list,
        description="参与的项目标签"
    )
    topic_interest_tags: List[str] = Field(
        default_factory=list,
        description="感兴趣的话题标签"
    )
    negative_feedback_tags: List[str] = Field(
        default_factory=list,
        description="负面反馈的话题标签（应减少推送）"
    )
    
    # 推送偏好
    push_preference: Dict[str, Any] = Field(
        default_factory=dict,
        description="推送偏好设置"
    )
    muted_topics: List[str] = Field(
        default_factory=list,
        description="静音的话题"
    )
    
    # 行为追踪
    recent_click_topics: List[str] = Field(
        default_factory=list,
        description="最近点击的话题"
    )
    recent_click_count: int = Field(
        default=0,
        description="近期点击总数"
    )
    
    # 活跃度
    last_active_at: Optional[datetime] = Field(
        default=None,
        description="最后活跃时间"
    )
    push_enabled: bool = Field(
        default=True,
        description="是否启用推送"
    )
    
    # 元数据
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="最后更新时间"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外元数据"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "user_001",
                    "role_tags": ["engineer", "tech_lead"],
                    "project_tags": ["proj_alpha", "proj_beta"],
                    "topic_interest_tags": ["architecture", "backend", "microservices"],
                    "negative_feedback_tags": ["marketing"],
                    "push_preference": {
                        "frequency": "daily",
                        "notify_hours": [9, 10, 14, 15, 16, 17]
                    },
                    "recent_click_topics": ["architecture"],
                    "push_enabled": True
                }
            ]
        }
    }
