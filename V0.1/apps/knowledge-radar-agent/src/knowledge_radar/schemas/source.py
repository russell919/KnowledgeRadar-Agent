"""
Source Schema - 来源对象定义

定义从飞书等系统同步的知识来源
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field


SourceType = Literal[
    "im",      # 即时通讯消息
    "doc",     # 云文档
    "calendar", # 日历/会议
    "task",    # 任务
    "base",    # 多维表格
    "wiki",    # 知识库
    "mail",    # 邮件
]


class SourceRef(BaseModel):
    """
    来源引用
    
    用于在推送内容中引用原始来源
    """
    source_id: str = Field(description="来源ID")
    source_type: SourceType = Field(description="来源类型")
    title: str = Field(description="来源标题")
    url: str = Field(description="来源URL")
    section_path: Optional[str] = Field(
        default=None,
        description="来源中的章节路径，如文档中的标题层级"
    )
    version: Optional[str] = Field(
        default=None,
        description="来源版本号"
    )
    update_time: Optional[datetime] = Field(
        default=None,
        description="最后更新时间"
    )
    author: Optional[str] = Field(
        default=None,
        description="作者/创建者"
    )


class SourceObject(BaseModel):
    """
    来源对象
    
    代表一个同步到知识雷达的原始对象
    """
    source_id: str = Field(description="来源唯一标识")
    source_type: SourceType = Field(description="来源类型")
    title: str = Field(description="对象标题")
    content: str = Field(description="对象主要内容")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="来源的元数据"
    )
    acl_tags: List[str] = Field(
        default_factory=list,
        description="访问控制标签，用于权限过滤"
    )
    version: str = Field(
        default="1.0",
        description="对象版本"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="首次同步时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="最后更新时间"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source_id": "doc_123456",
                    "source_type": "doc",
                    "title": "项目技术方案v2",
                    "content": "本文档描述了...",
                    "metadata": {
                        "doc_type": "docx",
                        "word_count": 3000,
                        "last_editor": "user_001"
                    },
                    "acl_tags": ["project_alpha", "tech_team"],
                    "version": "2.1",
                    "created_at": "2026-04-01T08:00:00Z",
                    "updated_at": "2026-04-30T10:00:00Z"
                }
            ]
        }
    }
