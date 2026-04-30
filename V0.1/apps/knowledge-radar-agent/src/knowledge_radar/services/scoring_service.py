"""
Scoring Service - 评分服务

计算知识推送的评分
"""

from typing import List, Dict, Any, Optional


class ScoringService:
    """
    评分服务
    
    实现多种评分功能：
    - score_weekly_importance: 周重要性评分
    - score_recipient_relevance: 接收人相关性评分
    - score_content_relevance: 内容相关性评分
    - score_doc_change_push: 文档变更推送评分
    - score_anti_disturbance_penalty: 打扰惩罚评分
    """
    
    def __init__(self):
        pass
    
    def score_weekly_importance(self, knowledge_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        计算周重要性评分
        
        Args:
            knowledge_items: 知识条目列表
        
        Returns:
            添加了评分的知识条目列表
        """
        scored = []
        
        for item in knowledge_items:
            score = 0.0
            
            # 知识类型权重
            type_weights = {
                "decision": 0.3,
                "action_item": 0.25,
                "risk": 0.25,
                "update": 0.15,
                "feedback": 0.05,
            }
            score += type_weights.get(item.get("knowledge_type"), 0.1)
            
            # 置信度
            confidence = item.get("confidence_score", 0.5)
            score *= confidence
            
            scored.append({**item, "weekly_importance_score": min(score, 1.0)})
        
        return scored
    
    def score_recipient_relevance(
        self,
        recipient_id: str,
        knowledge_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        计算接收人相关性评分
        
        Args:
            recipient_id: 接收人ID
            knowledge_items: 知识条目列表
        
        Returns:
            添加了相关性评分的知识条目列表
        """
        scored = []
        
        for item in knowledge_items:
            score = 0.5  # 基础分
            
            # 检查是否有明确关联
            if recipient_id in (item.get("related_users", [])):
                score += 0.3
            
            # 检查项目关联
            if item.get("project_id"):
                score += 0.1
            
            scored.append({**item, "recipient_relevance_score": min(score, 1.0)})
        
        return scored
    
    def score_content_relevance(
        self,
        query: str,
        knowledge_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        计算内容相关性评分
        
        Args:
            query: 查询文本
            knowledge_items: 知识条目列表
        
        Returns:
            添加了内容相关性评分的知识条目列表
        """
        scored = []
        
        for item in knowledge_items:
            text = (item.get("title", "") + " " + item.get("summary", "")).lower()
            query_words = set(query.lower().split())
            text_words = set(text.split())
            
            if not query_words:
                score = 0.5
            else:
                overlap = len(query_words & text_words) / len(query_words)
                score = 0.3 + overlap * 0.7
            
            scored.append({**item, "content_relevance_score": min(score, 1.0)})
        
        return scored
    
    def score_doc_change_push(
        self,
        change_units: List[Dict[str, Any]],
        recipient_id: str,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        计算文档变更推送评分
        
        公式：
        0.25*变更重要性 + 0.20*用户影响度 + 0.15*项目关联度 + 0.15*任务紧迫度 + 0.10*用户角色匹配度 + 0.10*信息新颖度 + 0.05*用户偏好适配度 - 0.10*打扰惩罚
        
        Args:
            change_units: 变更单元列表
            recipient_id: 接收人ID
            user_profile: 用户画像
        
        Returns:
            综合评分
        """
        # 1. 变更重要性 (25%)
        change_importance = self._calculate_change_importance(change_units)
        
        # 2. 用户影响度 (20%)
        user_impact = self._calculate_user_impact(change_units, recipient_id)
        
        # 3. 项目关联度 (15%)
        project_relevance = 0.7  # 占位值
        
        # 4. 任务紧迫度 (15%)
        task_urgency = 0.6  # 占位值
        
        # 5. 用户角色匹配度 (10%)
        role_match = self._calculate_role_match(recipient_id, user_profile)
        
        # 6. 信息新颖度 (10%)
        novelty = 0.8  # 占位值
        
        # 7. 用户偏好适配度 (5%)
        preference_fit = self._calculate_preference_fit(change_units, user_profile)
        
        # 8. 打扰惩罚 (-10%)
        disturbance_penalty = self._calculate_disturbance_penalty(recipient_id)
        
        # 综合评分
        score = (
            0.25 * change_importance +
            0.20 * user_impact +
            0.15 * project_relevance +
            0.15 * task_urgency +
            0.10 * role_match +
            0.10 * novelty +
            0.05 * preference_fit -
            0.10 * disturbance_penalty
        )
        
        return max(0, min(score, 1.0))
    
    def _calculate_change_importance(self, change_units: List[Dict[str, Any]]) -> float:
        """计算变更重要性"""
        if not change_units:
            return 0.0
        
        importance = 0.0
        for unit in change_units:
            change_type = unit.get("change_type")
            if change_type == "deleted":
                importance += 0.3
            elif change_type == "modified":
                importance += 0.2
            elif change_type == "added":
                importance += 0.1
        
        return min(importance / len(change_units), 1.0)
    
    def _calculate_user_impact(self, change_units: List[Dict[str, Any]], recipient_id: str) -> float:
        """计算用户影响度"""
        return 0.5  # 占位值
    
    def _calculate_role_match(self, recipient_id: str, user_profile: Optional[Dict[str, Any]]) -> float:
        """计算用户角色匹配度"""
        return 0.7  # 占位值
    
    def _calculate_preference_fit(self, change_units: List[Dict[str, Any]], user_profile: Optional[Dict[str, Any]]) -> float:
        """计算用户偏好适配度"""
        return 0.5  # 占位值
    
    def _calculate_disturbance_penalty(self, recipient_id: str) -> float:
        """计算打扰惩罚"""
        return 0.2  # 占位值
    
    def score_anti_disturbance_penalty(self, recipient_id: str, recent_pushes: int) -> float:
        """
        计算打扰惩罚评分
        
        Args:
            recipient_id: 接收人ID
            recent_pushes: 近期推送次数
        
        Returns:
            惩罚分数 (0-1)
        """
        if recent_pushes == 0:
            return 0.0
        elif recent_pushes <= 2:
            return 0.1
        elif recent_pushes <= 5:
            return 0.3
        else:
            return 0.5
