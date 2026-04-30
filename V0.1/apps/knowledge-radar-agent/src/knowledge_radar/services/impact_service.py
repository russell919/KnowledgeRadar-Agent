"""
Impact Service - 影响分析服务

分析变更对实体和用户的影响
"""

from typing import List, Dict, Any, Optional


class ImpactService:
    """
    影响分析服务
    
    根据 ChangeUnit 找受影响实体和候选接收人
    """
    
    def __init__(self, entity_repo, user_profile_repo):
        self.entity_repo = entity_repo
        self.user_profile_repo = user_profile_repo
    
    async def find_impacted_entities(
        self,
        change_units: List[Dict[str, Any]],
        project_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        查找受影响的实体
        
        Args:
            change_units: 变更单元列表
            project_ids: 项目ID列表
        
        Returns:
            受影响实体列表
        """
        impacted_entities = []
        
        for change in change_units:
            section_path = change.get("section_path", "")
            
            # 查找相关实体
            entities = await self.entity_repo.find_by_section(section_path, project_ids)
            impacted_entities.extend(entities)
        
        return impacted_entities
    
    async def find_candidate_recipients(
        self,
        change_units: List[Dict[str, Any]],
        project_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        查找候选接收人
        
        Args:
            change_units: 变更单元列表
            project_ids: 项目ID列表
        
        Returns:
            候选接收人列表，包含评分
        """
        recipients = {}
        
        # 1. 从项目关系获取
        project_members = await self._get_project_members(project_ids)
        for member in project_members:
            recipients[member["user_id"]] = self._init_recipient_score(member)
        
        # 2. 从任务 owner 获取
        task_owners = await self._get_task_owners(project_ids)
        for owner in task_owners:
            if owner["user_id"] in recipients:
                recipients[owner["user_id"]]["task_score"] += 0.3
            else:
                recipients[owner["user_id"]] = self._init_recipient_score(owner)
        
        # 3. 从文档编辑者获取
        editors = await self._get_document_editors(project_ids)
        for editor in editors:
            if editor["user_id"] in recipients:
                recipients[editor["user_id"]]["edit_score"] += 0.2
            else:
                recipients[editor["user_id"]] = self._init_recipient_score(editor)
        
        # 4. 从历史会议参与者获取
        participants = await self._get_meeting_participants(project_ids)
        for participant in participants:
            if participant["user_id"] in recipients:
                recipients[participant["user_id"]]["meeting_score"] += 0.15
            else:
                recipients[participant["user_id"]] = self._init_recipient_score(participant)
        
        # 5. 从显式订阅用户获取
        subscribers = await self._get_subscribers(project_ids)
        for subscriber in subscribers:
            if subscriber["user_id"] in recipients:
                recipients[subscriber["user_id"]]["subscription_score"] += 0.35
            else:
                recipients[subscriber["user_id"]] = self._init_recipient_score(subscriber)
        
        # 计算综合分数
        for user_id, score in recipients.items():
            score["total_score"] = sum([
                score["task_score"],
                score["edit_score"],
                score["meeting_score"],
                score["subscription_score"],
                score["project_score"],
            ])
        
        # 转换为列表并排序
        sorted_recipients = sorted(
            recipients.values(),
            key=lambda x: x["total_score"],
            reverse=True
        )
        
        return sorted_recipients
    
    def _init_recipient_score(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """初始化接收人分数"""
        return {
            "user_id": user_data.get("user_id"),
            "user_name": user_data.get("user_name"),
            "task_score": 0.0,
            "edit_score": 0.0,
            "meeting_score": 0.0,
            "subscription_score": 0.0,
            "project_score": 0.1,  # 基础分数
            "total_score": 0.1,
        }
    
    async def _get_project_members(self, project_ids: List[str]) -> List[Dict[str, Any]]:
        """获取项目成员（占位实现）"""
        return []
    
    async def _get_task_owners(self, project_ids: List[str]) -> List[Dict[str, Any]]:
        """获取任务所有者（占位实现）"""
        return []
    
    async def _get_document_editors(self, project_ids: List[str]) -> List[Dict[str, Any]]:
        """获取文档编辑者（占位实现）"""
        return []
    
    async def _get_meeting_participants(self, project_ids: List[str]) -> List[Dict[str, Any]]:
        """获取会议参与者（占位实现）"""
        return []
    
    async def _get_subscribers(self, project_ids: List[str]) -> List[Dict[str, Any]]:
        """获取订阅用户（占位实现）"""
        return []
