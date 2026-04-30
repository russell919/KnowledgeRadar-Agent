"""
Permission Service - 权限服务

处理权限检查和过滤
"""

from typing import List, Dict, Any, Optional


class PermissionService:
    """
    权限服务
    
    负责检查和过滤用户可访问的内容
    """
    
    def __init__(self):
        pass
    
    def filter_visible_items(
        self,
        user_id: str,
        items: List[Dict[str, Any]],
        user_acl_tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        过滤用户可见的项目
        
        Args:
            user_id: 用户ID
            items: 项目列表，每个项目应包含 'acl_tags' 字段
            user_acl_tags: 用户的 ACL 标签列表
        
        Returns:
            用户有权限访问的项目列表
        """
        if user_acl_tags is None:
            user_acl_tags = []
        
        visible_items = []
        for item in items:
            if self._has_access(user_acl_tags, item.get("acl_tags", [])):
                visible_items.append(item)
        
        return visible_items
    
    def _has_access(self, user_tags: List[str], item_tags: List[str]) -> bool:
        """
        检查用户是否有权限访问项目
        
        规则：
        - 如果项目没有 ACL 标签，所有人都可以访问
        - 如果用户有任何一个项目需要的标签，就可以访问
        """
        if not item_tags:
            return True
        
        for tag in user_tags:
            if tag in item_tags:
                return True
        
        return False
    
    def merge_permissions(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        合并多个项目的权限，取最严格的权限
        
        Args:
            items: 项目列表
        
        Returns:
            合并后的 ACL 标签列表（所有项目标签的交集）
        """
        if not items:
            return []
        
        all_tags = [set(item.get("acl_tags", [])) for item in items]
        if not all_tags:
            return []
        
        # 取交集 - 最严格的权限
        result_tags = set.intersection(*all_tags)
        return list(result_tags)
    
    def check_permission(
        self,
        user_acl_tags: List[str],
        required_tags: List[str],
    ) -> bool:
        """
        检查用户是否满足所需权限
        
        Args:
            user_acl_tags: 用户的 ACL 标签
            required_tags: 所需的权限标签
        
        Returns:
            是否有权限
        """
        if not required_tags:
            return True
        
        for tag in required_tags:
            if tag not in user_acl_tags:
                return False
        
        return True
