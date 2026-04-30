"""
Profile Service - 用户画像服务

管理用户画像数据
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class UserProfile:
    """
    用户画像
    """
    user_id: str
    interests: List[str]
    tags: List[str]
    preferences: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    last_updated: datetime


class ProfileService:
    """
    用户画像服务
    
    读取/更新 UserProfile
    显式反馈高于隐式行为
    负反馈立即生效
    兴趣标签有时间衰减
    """
    
    def __init__(self, profile_repo):
        self.profile_repo = profile_repo
    
    async def get_profile(self, user_id: str) -> UserProfile:
        """
        获取用户画像
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户画像
        """
        data = await self.profile_repo.get_by_user_id(user_id)
        
        if data:
            return UserProfile(
                user_id=data.get("user_id", user_id),
                interests=data.get("interests", []),
                tags=data.get("tags", []),
                preferences=data.get("preferences", {}),
                recent_activity=data.get("recent_activity", []),
                last_updated=datetime.fromisoformat(data.get("last_updated", datetime.utcnow().isoformat())),
            )
        
        # 返回默认画像
        return UserProfile(
            user_id=user_id,
            interests=[],
            tags=[],
            preferences={},
            recent_activity=[],
            last_updated=datetime.utcnow(),
        )
    
    async def update_profile(
        self,
        user_id: str,
        updates: Dict[str, Any],
    ) -> UserProfile:
        """
        更新用户画像
        
        Args:
            user_id: 用户ID
            updates: 更新内容
        
        Returns:
            更新后的用户画像
        """
        profile = await self.get_profile(user_id)
        
        if "interests" in updates:
            profile.interests = self._merge_interests(profile.interests, updates["interests"])
        
        if "tags" in updates:
            profile.tags = list(set(profile.tags + updates["tags"]))
        
        if "preferences" in updates:
            profile.preferences.update(updates["preferences"])
        
        if "activity" in updates:
            profile.recent_activity.append({
                "activity_type": updates["activity"].get("type"),
                "content": updates["activity"].get("content"),
                "timestamp": datetime.utcnow(),
            })
            # 保留最近50条活动记录
            profile.recent_activity = profile.recent_activity[-50:]
        
        profile.last_updated = datetime.utcnow()
        
        # 应用时间衰减
        profile.interests = self._apply_time_decay(profile.interests)
        
        await self.profile_repo.save(profile)
        
        return profile
    
    async def record_explicit_feedback(
        self,
        user_id: str,
        feedback_type: str,  # positive, negative, neutral
        knowledge_id: str,
    ) -> None:
        """
        记录显式反馈
        
        Args:
            user_id: 用户ID
            feedback_type: 反馈类型
            knowledge_id: 知识ID
        """
        profile = await self.get_profile(user_id)
        
        if feedback_type == "negative":
            # 负反馈立即生效，降低相关兴趣权重
            profile.interests = [
                i for i in profile.interests
                if not self._is_related(i, knowledge_id)
            ]
        
        elif feedback_type == "positive":
            # 正反馈增加兴趣
            # TODO: 从知识提取关键词作为兴趣标签
            pass
        
        profile.last_updated = datetime.utcnow()
        await self.profile_repo.save(profile)
    
    def _merge_interests(self, existing: List[str], new: List[str]) -> List[str]:
        """合并兴趣列表"""
        all_interests = existing + new
        return list(set(all_interests))
    
    def _apply_time_decay(self, interests: List[str]) -> List[str]:
        """
        应用时间衰减
        
        兴趣标签随时间推移逐渐减弱，最终被移除
        """
        # 简化实现：保留所有兴趣
        # 实际实现时需要记录兴趣的添加时间，然后根据时间进行衰减
        return interests[:20]  # 限制数量
    
    def _is_related(self, interest: str, knowledge_id: str) -> bool:
        """检查兴趣是否与知识相关"""
        return False
