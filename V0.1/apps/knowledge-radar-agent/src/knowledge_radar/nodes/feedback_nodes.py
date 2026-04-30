"""
Feedback Nodes - 反馈节点
"""

from typing import Dict, Any
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def normalize_feedback(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    规范化反馈
    
    输入: feedback
    输出: normalized_feedback
    """
    feedback = state.scene_context.get("feedback", {})
    
    return {
        "normalized_feedback": {
            "feedback_type": feedback.get("type", "implicit"),
            "knowledge_id": feedback.get("knowledge_id", ""),
            "rating": feedback.get("rating", 0),
            "comment": feedback.get("comment", ""),
            "timestamp": feedback.get("timestamp", ""),
        }
    }


async def classify_feedback(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    分类反馈
    
    输入: normalized_feedback
    输出: feedback_class, action
    """
    rating = state.normalized_feedback.get("rating", 0)
    
    if rating >= 4:
        feedback_class = "positive"
        action = "increase_interest"
    elif rating <= 2:
        feedback_class = "negative"
        action = "decrease_interest"
    else:
        feedback_class = "neutral"
        action = "no_change"
    
    return {"feedback_class": feedback_class, "action": action}


async def update_user_profile(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    更新用户画像
    
    输入: user_id, profile_delta
    输出: updated_profile
    """
    from knowledge_radar.services import ProfileService
    
    class MockProfileRepo:
        async def get_by_user_id(self, uid):
            return {"user_id": uid, "interests": [], "tags": []}
        async def save(self, profile):
            pass
    
    service = ProfileService(MockProfileRepo())
    
    try:
        updated = await service.update_profile(state.user_id, state.profile_delta)
        return {"updated_profile": {"user_id": updated.user_id, "interests": updated.interests}}
    except:
        return {"updated_profile": {"user_id": state.user_id}}
