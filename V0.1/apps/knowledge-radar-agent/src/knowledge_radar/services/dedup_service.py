"""
Dedup Service - 去重服务

处理知识条目和文档的去重
"""

from typing import List, Dict, Any, Optional
from hashlib import md5


class DedupService:
    """
    去重服务
    
    使用多种策略进行去重：
    - 内容哈希去重
    - 语义相似度去重
    - 标题+摘要去重
    """
    
    def __init__(self, threshold: float = 0.9):
        self.threshold = threshold  # 相似度阈值
    
    def deduplicate_by_hash(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用内容哈希去重
        
        Args:
            items: 项目列表，每个项目应包含 'content' 字段
        
        Returns:
            去重后的项目列表
        """
        seen_hashes = set()
        unique_items = []
        
        for item in items:
            content = item.get("content", "") + item.get("title", "")
            content_hash = md5(content.encode()).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_items.append(item)
        
        return unique_items
    
    def deduplicate_by_similarity(
        self,
        items: List[Dict[str, Any]],
        similarity_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        使用语义相似度去重
        
        Args:
            items: 项目列表
            similarity_threshold: 相似度阈值
        
        Returns:
            去重后的项目列表
        """
        threshold = similarity_threshold or self.threshold
        
        if len(items) <= 1:
            return items
        
        unique_items = []
        
        for i, item_i in enumerate(items):
            is_duplicate = False
            
            for item_j in unique_items:
                similarity = self._calculate_similarity(item_i, item_j)
                if similarity >= threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item_i)
        
        return unique_items
    
    def _calculate_similarity(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> float:
        """
        计算两个项目的相似度
        
        Args:
            item1: 项目1
            item2: 项目2
        
        Returns:
            相似度分数 (0-1)
        """
        text1 = (item1.get("title", "") + " " + item1.get("summary", "") + " " + item1.get("content", "")).lower()
        text2 = (item2.get("title", "") + " " + item2.get("summary", "") + " " + item2.get("content", "")).lower()
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union
