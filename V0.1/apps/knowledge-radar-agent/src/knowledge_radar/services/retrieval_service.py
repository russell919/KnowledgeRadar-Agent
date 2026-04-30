"""
Retrieval Service - 检索服务

实现混合检索：ACL过滤、结构化过滤、向量召回、全文召回、关系扩展召回
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """
    检索结果
    """
    knowledge_id: str
    score: float
    title: str
    summary: str
    source_refs: List[Dict[str, Any]]
    acl_tags: List[str]


class RetrievalService:
    """
    检索服务
    
    实现 hybrid retrieval：
    - ACL 过滤
    - 结构化过滤
    - 向量召回
    - 全文召回
    - 关系扩展召回
    - 合并去重
    """
    
    def __init__(
        self,
        knowledge_repo,
        embedding_client,
        permission_service,
        rerank_client,
    ):
        self.knowledge_repo = knowledge_repo
        self.embedding_client = embedding_client
        self.permission_service = permission_service
        self.rerank_client = rerank_client
    
    async def retrieve(
        self,
        query: str,
        user_id: str,
        user_acl_tags: List[str],
        project_ids: Optional[List[str]] = None,
        knowledge_types: Optional[List[str]] = None,
        top_k: int = 10,
    ) -> List[RetrievalResult]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            user_id: 用户ID
            user_acl_tags: 用户 ACL 标签
            project_ids: 项目ID列表（可选）
            knowledge_types: 知识类型列表（可选）
            top_k: 返回数量
        
        Returns:
            检索结果列表
        """
        # 1. 向量召回
        vector_results = await self._vector_search(query, top_k * 2)
        
        # 2. 全文召回
        fulltext_results = self._fulltext_search(query, top_k * 2)
        
        # 3. 结构化过滤
        filtered_results = self._structured_filter(
            vector_results + fulltext_results,
            project_ids,
            knowledge_types,
        )
        
        # 4. ACL 过滤
        visible_results = self.permission_service.filter_visible_items(
            user_id,
            filtered_results,
            user_acl_tags,
        )
        
        # 5. 去重
        deduplicated = self._deduplicate(visible_results)
        
        # 6. 重排序
        reranked = await self._rerank(query, deduplicated)
        
        # 7. 关系扩展
        extended = await self._relation_expand(reranked, user_id)
        
        # 8. 最终排序和截断
        final_results = self._final_sort(extended)[:top_k]
        
        return [self._to_result(item) for item in final_results]
    
    async def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """向量搜索"""
        # TODO: 实际实现时调用向量数据库
        return []
    
    def _fulltext_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """全文搜索"""
        # TODO: 实际实现时调用全文索引
        return []
    
    def _structured_filter(
        self,
        results: List[Dict[str, Any]],
        project_ids: Optional[List[str]],
        knowledge_types: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """结构化过滤"""
        filtered = results
        
        if project_ids:
            filtered = [
                r for r in filtered
                if any(p in (r.get("project_ids", [])) for p in project_ids)
            ]
        
        if knowledge_types:
            filtered = [
                r for r in filtered
                if r.get("knowledge_type") in knowledge_types
            ]
        
        return filtered
    
    def _deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重"""
        seen = set()
        unique = []
        
        for r in results:
            kid = r.get("knowledge_id")
            if kid not in seen:
                seen.add(kid)
                unique.append(r)
        
        return unique
    
    async def _rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重排序"""
        if not results:
            return []
        
        documents = [{"text": r.get("summary", "") + " " + r.get("title", ""), **r} for r in results]
        reranked = await self.rerank_client.rerank(query, documents, len(results))
        
        return [r.document for r in reranked]
    
    async def _relation_expand(self, results: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """关系扩展召回"""
        # TODO: 从实体关系表扩展相关知识
        return results
    
    def _final_sort(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """最终排序"""
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    
    def _to_result(self, item: Dict[str, Any]) -> RetrievalResult:
        """转换为检索结果对象"""
        return RetrievalResult(
            knowledge_id=item.get("knowledge_id", ""),
            score=item.get("score", 0),
            title=item.get("title", ""),
            summary=item.get("summary", ""),
            source_refs=item.get("source_refs", []),
            acl_tags=item.get("acl_tags", []),
        )
