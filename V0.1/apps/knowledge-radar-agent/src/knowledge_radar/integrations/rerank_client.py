"""
Rerank Client - 重排序客户端

封装与 Rerank 服务的通信
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class RerankResult:
    """
    重排序结果
    """
    document: Dict[str, Any]
    score: float


class RerankClient:
    """
    Rerank 客户端
    
    提供文档重排序功能
    如果没有真实 rerank 模型，使用 fallback：关键词 + cosine + source authority
    """
    
    def __init__(self, use_fallback: bool = True):
        self.use_fallback = use_fallback
    
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
            documents: 文档列表，每个文档应包含 'text' 字段
            top_k: 返回前 K 个结果
        
        Returns:
            重排序后的结果列表
        """
        if not documents:
            return []
        
        if self.use_fallback:
            return self._fallback_rerank(query, documents, top_k)
        
        return await self._call_rerank_api(query, documents, top_k)
    
    async def _call_rerank_api(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int],
    ) -> List[RerankResult]:
        """
        调用真实的 Rerank API
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量
        
        Returns:
            重排序结果
        """
        # TODO: 实际实现时调用真实的 Rerank API
        # 例如 Cohere Rerank 或其他服务
        return self._fallback_rerank(query, documents, top_k)
    
    def _fallback_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int],
    ) -> List[RerankResult]:
        """
        Fallback 重排序策略：关键词匹配 + 余弦相似度 + 来源权威性
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量
        
        Returns:
            重排序结果
        """
        results = []
        
        query_words = set(query.lower().split())
        
        for doc in documents:
            text = doc.get("text", "") + " " + doc.get("title", "")
            text_words = set(text.lower().split())
            
            # 关键词匹配得分 (30%)
            keyword_score = self._calculate_keyword_match(query_words, text_words)
            
            # 余弦相似度得分 (40%)
            cosine_score = self._calculate_cosine_similarity(query, text)
            
            # 来源权威性得分 (30%)
            authority_score = doc.get("authority_score", 0.5)
            
            # 综合得分
            total_score = (
                0.3 * keyword_score +
                0.4 * cosine_score +
                0.3 * authority_score
            )
            
            results.append(RerankResult(
                document=doc,
                score=total_score,
            ))
        
        # 排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 截断
        if top_k:
            results = results[:top_k]
        
        return results
    
    def _calculate_keyword_match(self, query_words: set, text_words: set) -> float:
        """
        计算关键词匹配得分
        
        Args:
            query_words: 查询词集合
            text_words: 文本词集合
        
        Returns:
            匹配得分 (0-1)
        """
        if not query_words:
            return 0.5
        
        intersection = len(query_words & text_words)
        return intersection / len(query_words)
    
    def _calculate_cosine_similarity(self, query: str, text: str) -> float:
        """
        计算余弦相似度（简化版）
        
        Args:
            query: 查询文本
            text: 文档文本
        
        Returns:
            相似度得分 (0-1)
        """
        query_vec = self._text_to_vector(query)
        text_vec = self._text_to_vector(text)
        
        dot_product = sum(query_vec.get(k, 0) * text_vec.get(k, 0) for k in query_vec)
        query_norm = math.sqrt(sum(v ** 2 for v in query_vec.values()))
        text_norm = math.sqrt(sum(v ** 2 for v in text_vec.values()))
        
        if query_norm == 0 or text_norm == 0:
            return 0.0
        
        return dot_product / (query_norm * text_norm)
    
    def _text_to_vector(self, text: str) -> Dict[str, int]:
        """
        将文本转换为词频向量
        
        Args:
            text: 文本
        
        Returns:
            词频向量
        """
        words = text.lower().split()
        vector = {}
        
        for word in words:
            vector[word] = vector.get(word, 0) + 1
        
        return vector
