"""
Safety Service - 安全服务

检查输出的安全性和合规性
"""

from typing import List, Dict, Any, Optional


class SafetyService:
    """
    安全服务
    
    检查：
    - source_refs 是否有效
    - 权限是否足够
    - 是否需要 human_preview
    - 输出是否包含无来源结论
    """
    
    def __init__(self):
        pass
    
    def check_output(
        self,
        output: Dict[str, Any],
        user_id: str,
        user_acl_tags: List[str],
    ) -> Dict[str, Any]:
        """
        检查输出的安全性
        
        Args:
            output: 输出内容
            user_id: 用户ID
            user_acl_tags: 用户ACL标签
        
        Returns:
            检查结果
        """
        checks = []
        
        # 检查来源引用
        source_check = self._check_source_refs(output.get("source_refs", []))
        checks.append(source_check)
        
        # 检查权限
        acl_check = self._check_permissions(output, user_acl_tags)
        checks.append(acl_check)
        
        # 检查是否需要人工预览
        preview_check = self._check_requires_human_preview(output)
        checks.append(preview_check)
        
        # 检查无来源结论
        conclusion_check = self._check_unattributed_conclusions(output)
        checks.append(conclusion_check)
        
        # 综合结果
        all_passed = all(check["passed"] for check in checks)
        requires_review = any(check.get("requires_review", False) for check in checks)
        
        return {
            "safe": all_passed,
            "requires_review": requires_review,
            "checks": checks,
        }
    
    def _check_source_refs(self, source_refs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        检查来源引用
        
        Args:
            source_refs: 来源引用列表
        
        Returns:
            检查结果
        """
        if not source_refs:
            return {
                "name": "source_refs",
                "passed": False,
                "reason": "缺少来源引用",
            }
        
        valid_refs = [ref for ref in source_refs if self._validate_ref(ref)]
        
        if len(valid_refs) < len(source_refs):
            return {
                "name": "source_refs",
                "passed": False,
                "reason": f"部分来源引用无效",
            }
        
        return {
            "name": "source_refs",
            "passed": True,
            "reason": "所有来源引用有效",
        }
    
    def _validate_ref(self, ref: Dict[str, Any]) -> bool:
        """验证单个来源引用"""
        required_fields = ["source_id", "source_type"]
        
        for field in required_fields:
            if not ref.get(field):
                return False
        
        return True
    
    def _check_permissions(
        self,
        output: Dict[str, Any],
        user_acl_tags: List[str],
    ) -> Dict[str, Any]:
        """
        检查权限
        
        Args:
            output: 输出内容
            user_acl_tags: 用户ACL标签
        
        Returns:
            检查结果
        """
        required_tags = output.get("acl_tags", [])
        
        if not required_tags:
            return {
                "name": "permissions",
                "passed": True,
                "reason": "无需特殊权限",
            }
        
        for tag in required_tags:
            if tag not in user_acl_tags:
                return {
                    "name": "permissions",
                    "passed": False,
                    "reason": f"缺少必要权限标签: {tag}",
                }
        
        return {
            "name": "permissions",
            "passed": True,
            "reason": "权限检查通过",
        }
    
    def _check_requires_human_preview(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查是否需要人工预览
        
        Args:
            output: 输出内容
        
        Returns:
            检查结果
        """
        content = output.get("content", "")
        
        # 检查敏感关键词
        sensitive_keywords = [
            "机密",
            "保密",
            "内部",
            "战略",
            "财务",
            "薪资",
            "人事",
        ]
        
        for keyword in sensitive_keywords:
            if keyword in content:
                return {
                    "name": "human_preview",
                    "passed": True,
                    "requires_review": True,
                    "reason": f"检测到敏感内容: {keyword}",
                }
        
        return {
            "name": "human_preview",
            "passed": True,
            "requires_review": False,
            "reason": "无需人工预览",
        }
    
    def _check_unattributed_conclusions(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查是否包含无来源结论
        
        Args:
            output: 输出内容
        
        Returns:
            检查结果
        """
        content = output.get("content", "")
        
        # 检测无来源结论的模式
        conclusion_patterns = [
            "我们决定",
            "应该",
            "建议",
            "必须",
            "结论是",
        ]
        
        source_refs = output.get("source_refs", [])
        
        if source_refs:
            return {
                "name": "unattributed_conclusions",
                "passed": True,
                "reason": "已有来源引用",
            }
        
        for pattern in conclusion_patterns:
            if pattern in content:
                return {
                    "name": "unattributed_conclusions",
                    "passed": False,
                    "reason": f"检测到无来源结论: {pattern}",
                }
        
        return {
            "name": "unattributed_conclusions",
            "passed": True,
            "reason": "未检测到无来源结论",
        }
