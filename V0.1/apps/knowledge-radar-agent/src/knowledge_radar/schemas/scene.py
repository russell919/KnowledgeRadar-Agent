"""
Scene Schema - 场景上下文定义

定义知识雷达 Agent 运行的场景信息
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field


SceneType = Literal[
    "weekly_digest",     # 每周知识推送
    "meeting_briefing",  # 会前简报
    "doc_change",        # 文档变更
    "onboarding",        # 新人入职/入组
    "manual",           # 手动触发
]


class SceneContext(BaseModel):
    """
    场景上下文
    
    描述 Agent 运行的当前场景信息
    """
    scene_type: SceneType = Field(description="场景类型")
    
    # 范围限定
    project_ids: List[str] = Field(
        default_factory=list,
        description="相关的项目ID列表"
    )
    user_ids: List[str] = Field(
        default_factory=list,
        description="目标用户ID列表"
    )
    group_ids: List[str] = Field(
        default_factory=list,
        description="目标群组ID列表"
    )
    
    # 时间窗口
    time_window: Optional[Dict[str, datetime]] = Field(
        default=None,
        description="时间窗口，如过去一周"
    )
    
    # 紧急程度
    urgency: str = Field(
        default="normal",
        description="紧急程度: low, normal, high, critical"
    )
    
    # 知识需求
    required_knowledge_types: List[str] = Field(
        default_factory=list,
        description="需要的知识类型"
    )
    
    # LLM 生成内容
    explanation: Optional[str] = Field(
        default=None,
        description="场景解释/LLM生成的分析"
    )
    evidence_refs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="支撑证据引用"
    )
    
    # 元数据
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外场景元数据"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scene_type": "meeting_briefing",
                    "project_ids": ["proj_alpha"],
                    "user_ids": ["user_001"],
                    "group_ids": [],
                    "time_window": {
                        "start": "2026-04-23T00:00:00Z",
                        "end": "2026-04-30T12:00:00Z"
                    },
                    "urgency": "normal",
                    "required_knowledge_types": ["decision", "action_item", "update"],
                    "explanation": "为明天14:00的项目周会准备简报..."
                }
            ]
        }
    }
