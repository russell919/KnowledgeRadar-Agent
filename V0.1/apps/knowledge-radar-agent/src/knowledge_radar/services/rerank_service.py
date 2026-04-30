"""
Rerank Service - 重排序服务

对检索结果进行重排序
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RerankResult:
    """
    重排序结果
    """
    knowledge_id: str
    rank: int
    score: float
    title: str
    summary: str


class RerankService:
    """
    重排序服务
    
    使用多种策略进行重排序：
    - LLM 重排序
    - 关键词匹配
    - 语义相似度
    - 来源权威性
    """
    
    def __init__(self, rerank_client):
        self.rerank_client = rerank_client
    
    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[RerankResult]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档应包含 'text' 或 'summary' 字段
            top_k: 返回前 K 个结果
        
        Returns:
            重排序后的结果列表
        """
        if not documents:
            return []
        
        # 准备输入格式
        input_docs = []
        for doc in documents:
            text = doc.get("text", "") or doc.get("summary", "") or doc.get("title", "")
            input_docs.append({
                "text": text,
                "knowledge_id": doc.get("knowledge_id"),
                "title": doc.get("title", ""),
                "summary": doc.get("summary", ""),
                "authority_score": doc.get("authority_score", 0.5),
            })
        
        # 调用重排序客户端
        results = await self.rerank_client.rerank(query, input_docs, top_k)
        
        # 转换格式
        return [RerankResult(
            knowledge_id=r.document.get("knowledge_id", ""),
            rank=i + 1,
            score=r.score,
            title=r.document.get("title", ""),
            summary=r.document.get("summary", ""),
        ) for i, r in enumerate(results)]
