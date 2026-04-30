"""
Validity Service - 有效性服务

验证知识的有效性和时效性
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class ValidityService:
    """
    有效性服务
    
    验证知识的有效性、时效性、准确性
    """
    
    def __init__(self):
        pass
    
    def is_valid(self, knowledge: Dict[str, Any]) -> bool:
        """
        检查知识是否有效
        
        Args:
            knowledge: 知识条目
        
        Returns:
            是否有效
        """
        # 检查状态
        if knowledge.get("status") == "deleted":
            return False
        
        # 检查时间有效性
        valid_from = knowledge.get("valid_from")
        valid_to = knowledge.get("valid_to")
        now = datetime.utcnow()
        
        if valid_from and datetime.fromisoformat(valid_from) > now:
            return False
        
        if valid_to and datetime.fromisoformat(valid_to) < now:
            return False
        
        # 检查置信度
        confidence = knowledge.get("confidence_score", 0.5)
        if confidence < 0.3:
            return False
        
        return True
    
    def filter_valid_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤有效项目
        
        Args:
            items: 项目列表
        
        Returns:
            有效的项目列表
        """
        return [item for item in items if self.is_valid(item)]
    
    def validate_knowledge(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证知识并返回验证结果
        
        Args:
            knowledge: 知识条目
        
        Returns:
            验证结果，包含 valid 和 reasons
        """
        reasons = []
        valid = True
        
        if knowledge.get("status") == "deleted":
            reasons.append("知识已删除")
            valid = False
        
        now = datetime.utcnow()
        valid_from = knowledge.get("valid_from")
        if valid_from and datetime.fromisoformat(valid_from) > now:
            reasons.append(f"知识尚未生效（生效时间：{valid_from}）")
            valid = False
        
        valid_to = knowledge.get("valid_to")
        if valid_to and datetime.fromisoformat(valid_to) < now:
            reasons.append(f"知识已过期（过期时间：{valid_to}）")
            valid = False
        
        confidence = knowledge.get("confidence_score", 0.5)
        if confidence < 0.3:
            reasons.append(f"置信度过低（{confidence}）")
            valid = False
        
        return {
            "valid": valid,
            "reasons": reasons,
            "knowledge": knowledge,
        }
