"""
State Schema - LangGraph 状态定义

定义知识雷达 Agent 的完整运行状态
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from knowledge_radar.schemas.trigger import Trigger, TriggerType
from knowledge_radar.schemas.scene import SceneContext
from knowledge_radar.schemas.source import SourceRef
from knowledge_radar.schemas.knowledge import KnowledgeItem, KnowledgeChunk
from knowledge_radar.schemas.retrieval import RetrievalResult
from knowledge_radar.schemas.profile import UserProfile
from knowledge_radar.schemas.push import RankingResult
from knowledge_radar.schemas.cards import OutputCard, FeishuCardPayload
from knowledge_radar.schemas.feedback import FeedbackEvent


class KnowledgeRadarState(BaseModel):
    """
    知识雷达 Agent 状态
    
    这是 LangGraph StateGraph 的核心状态对象
    在整个 Agent 执行过程中流动和更新
    """
    # ========== 基础信息 ==========
    run_id: str = Field(description="本次运行唯一ID")
    
    # ========== 触发器 ==========
    trigger: Optional[Trigger] = Field(
        default=None,
        description="触发器信息"
    )
    
    # ========== 场景上下文 ==========
    scene: Optional[SceneContext] = Field(
        default=None,
        description="场景上下文"
    )
    
    # ========== 权限信息 ==========
    permissions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="权限信息: user_id -> acl_tags"
    )
    
    # ========== 原始上下文 ==========
    raw_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="从飞书等系统拉取的原始数据"
    )
    
    # ========== 知识候选 ==========
    knowledge_candidates: List[KnowledgeItem] = Field(
        default_factory=list,
        description="知识候选列表"
    )
    
    # ========== 检索结果 ==========
    retrieval_result: Optional[RetrievalResult] = Field(
        default=None,
        description="检索结果"
    )
    
    # ========== 用户画像 ==========
    user_profiles: Dict[str, UserProfile] = Field(
        default_factory=dict,
        description="用户画像字典: user_id -> profile"
    )
    
    # ========== 排序结果 ==========
    ranking_result: Optional[RankingResult] = Field(
        default=None,
        description="推送排序结果"
    )
    
    # ========== 输出 ==========
    output: Optional[OutputCard] = Field(
        default=None,
        description="最终输出卡片"
    )
    feishu_payload: Optional[FeishuCardPayload] = Field(
        default=None,
        description="飞书卡片 payload"
    )
    
    # ========== 反馈 ==========
    feedback: Optional[FeedbackEvent] = Field(
        default=None,
        description="用户反馈"
    )
    
    # ========== 错误和日志 ==========
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="执行过程中的错误"
    )
    logs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="执行日志"
    )
    
    # ========== 执行控制 ==========
    dry_run: bool = Field(
        default=False,
        description="是否为预览模式"
    )
    human_preview: bool = Field(
        default=True,
        description="是否需要人工预览"
    )
    
    # ========== 元数据 ==========
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )
    
    def add_error(self, error_type: str, message: str, details: Dict[str, Any] = None):
        """添加错误"""
        self.errors.append({
            "type": error_type,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def add_log(self, step: str, message: str, data: Dict[str, Any] = None):
        """添加日志"""
        self.logs.append({
            "step": step,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "run_id": "run_123456",
                    "trigger": {
                        "trigger_type": "meeting_briefing",
                        "source_id": "meeting_789",
                        "workspace_id": "ws_001"
                    },
                    "scene": {
                        "scene_type": "meeting_briefing",
                        "project_ids": ["proj_alpha"],
                        "urgency": "normal"
                    },
                    "knowledge_candidates": [],
                    "user_profiles": {},
                    "dry_run": False,
                    "human_preview": True
                }
            ]
        }
    }
