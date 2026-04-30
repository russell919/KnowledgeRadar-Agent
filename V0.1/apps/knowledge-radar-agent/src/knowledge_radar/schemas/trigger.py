"""
Trigger Schema - 触发器定义

定义知识雷达 Agent 的触发器类型和数据结构
"""

from datetime import datetime
from typing import Optional, Dict, Any, Literal

from pydantic import BaseModel, Field


TriggerType = Literal[
    "weekly_digest",   # 每周知识推送
    "meeting_briefing",  # 会前简报
    "doc_change",       # 文档变更提醒
    "onboarding",       # 新人入职引导
    "manual",           # 手动触发
]


class Trigger(BaseModel):
    """
    触发器数据模型
    
    描述触发知识雷达 Agent 运行的事件或条件
    """
    trigger_type: TriggerType = Field(
        description="触发类型"
    )
    source_id: Optional[str] = Field(
        default=None,
        description="触发源ID，如会议ID、文档ID等"
    )
    workspace_id: str = Field(
        description="工作空间ID"
    )
    operator_user_id: Optional[str] = Field(
        default=None,
        description="触发操作者用户ID"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="触发时间"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="触发器携带的额外数据"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "trigger_type": "meeting_briefing",
                    "source_id": "meeting_123456",
                    "workspace_id": "ws_001",
                    "operator_user_id": "user_001",
                    "timestamp": "2026-04-30T10:00:00Z",
                    "payload": {
                        "meeting_title": "项目周会",
                        "attendees": ["user_001", "user_002"],
                        "meeting_start_time": "2026-04-30T14:00:00Z"
                    }
                }
            ]
        }
    }
