"""
Knowledge Schema - 知识条目定义

定义从来源中提取、提炼的结构化知识
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field

from knowledge_radar.schemas.source import SourceRef


KnowledgeType = Literal[
    "decision",         # 决策记录
    "action_item",      # 行动项/待办
    "risk",             # 风险点
    "update",           # 重要更新
    "feedback",         # 用户反馈
    "faq_candidate",    # FAQ候选
    "reference",        # 参考资料
    "project_profile",  # 项目概况
]


class KnowledgeChunk(BaseModel):
    """
    知识块
    
    知识条目的语义分块，用于向量检索
    """
    chunk_id: str = Field(description="分块唯一ID")
    knowledge_id: str = Field(description="所属知识条目ID")
    chunk_text: str = Field(description="分块文本内容")
    section_path: Optional[str] = Field(
        default=None,
        description="在原始文档中的章节路径"
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        description="分块的向量嵌入"
    )
    source_ref: Optional[SourceRef] = Field(
        default=None,
        description="分块对应的来源引用"
    )
    acl_tags: List[str] = Field(
        default_factory=list,
        description="访问控制标签"
    )


class KnowledgeItem(BaseModel):
    """
    知识条目
    
    从来源中提取的结构化知识单元
    """
    knowledge_id: str = Field(description="知识条目唯一ID")
    knowledge_type: KnowledgeType = Field(description="知识类型")
    title: str = Field(description="知识标题")
    summary: str = Field(description="知识摘要/一句话总结")
    content: str = Field(description="知识详细内容")
    
    # 关联信息
    project_ids: List[str] = Field(
        default_factory=list,
        description="关联的项目ID列表"
    )
    related_user_ids: List[str] = Field(
        default_factory=list,
        description="相关用户ID列表"
    )
    related_task_ids: List[str] = Field(
        default_factory=list,
        description="关联的任务ID列表"
    )
    source_refs: List[SourceRef] = Field(
        default_factory=list,
        description="知识来源引用"
    )
    
    # 质量评分
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="置信度评分"
    )
    authority_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="权威性评分"
    )
    
    # 状态和时间
    status: str = Field(
        default="active",
        description="状态: active, archived, deleted"
    )
    valid_from: Optional[datetime] = Field(
        default=None,
        description="有效开始时间"
    )
    valid_to: Optional[datetime] = Field(
        default=None,
        description="有效结束时间"
    )
    
    # 时间戳
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "knowledge_id": "ki_123456",
                    "knowledge_type": "decision",
                    "title": "采用微服务架构",
                    "summary": "决定采用微服务架构进行系统重构",
                    "content": "经过技术方案对比，决定采用微服务架构...",
                    "project_ids": ["proj_alpha"],
                    "related_user_ids": ["user_001", "user_002"],
                    "confidence_score": 0.9,
                    "authority_score": 0.8,
                    "status": "active"
                }
            ]
        }
    }
