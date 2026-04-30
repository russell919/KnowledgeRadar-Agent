"""
Retrieval Schema - 检索定义

定义知识检索的查询和结果结构
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from knowledge_radar.schemas.knowledge import KnowledgeItem, KnowledgeChunk
from knowledge_radar.schemas.source import SourceRef


class RetrievalQuery(BaseModel):
    """
    检索查询
    
    描述用户的检索需求
    """
    query_text: str = Field(description="检索文本")
    query_embedding: Optional[List[float]] = Field(
        default=None,
        description="检索向量（可选）"
    )
    
    # 范围限定
    project_ids: List[str] = Field(
        default_factory=list,
        description="限定在某些项目中检索"
    )
    knowledge_types: List[str] = Field(
        default_factory=list,
        description="限定知识类型"
    )
    user_ids: List[str] = Field(
        default_factory=list,
        description="限定相关用户"
    )
    
    # 权限过滤
    acl_tags: List[str] = Field(
        default_factory=list,
        description="当前用户的访问标签"
    )
    
    # 检索参数
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="返回结果数量"
    )
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="最低相关度分数"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外检索参数"
    )


class RetrievalHit(BaseModel):
    """
    检索命中
    
    表示一条检索结果
    """
    rank: int = Field(description="排名")
    score: float = Field(description="相关度分数")
    score_type: str = Field(
        default="combined",
        description="分数类型: vector, bm25, combined"
    )
    
    knowledge_item: KnowledgeItem = Field(description="命中的知识条目")
    matched_chunks: List[KnowledgeChunk] = Field(
        default_factory=list,
        description="匹配的知识块"
    )
    highlights: List[str] = Field(
        default_factory=list,
        description="高亮片段"
    )


class RetrievalResult(BaseModel):
    """
    检索结果
    
    包含多条检索命中的完整结果
    """
    query: RetrievalQuery = Field(description="原始查询")
    hits: List[RetrievalHit] = Field(
        default_factory=list,
        description="检索命中列表"
    )
    total_hits: int = Field(description="总命中数")
    retrieval_time_ms: float = Field(description="检索耗时（毫秒）")
    
    # 统计信息
    scores: Dict[str, float] = Field(
        default_factory=dict,
        description="各类型分数统计"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": {
                        "query_text": "项目架构决策",
                        "top_k": 5
                    },
                    "hits": [
                        {
                            "rank": 1,
                            "score": 0.95,
                            "knowledge_item": {
                                "knowledge_id": "ki_123",
                                "knowledge_type": "decision",
                                "title": "采用微服务架构"
                            },
                            "matched_chunks": [],
                            "highlights": ["决定采用微服务架构"]
                        }
                    ],
                    "total_hits": 1,
                    "retrieval_time_ms": 15.3
                }
            ]
        }
    }
