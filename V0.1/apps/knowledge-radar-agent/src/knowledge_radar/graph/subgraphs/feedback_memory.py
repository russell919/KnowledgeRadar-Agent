"""
Feedback Memory Subgraph - 反馈记忆子图

处理用户反馈并更新记忆
"""

from typing import Dict, Any, Callable
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


def build_feedback_memory_subgraph() -> Dict[str, Callable]:
    """
    构建反馈记忆子图
    
    流程：
    normalize_feedback → classify_feedback → build_profile_delta
    → update_user_profile → update_knowledge_usefulness → detect_high_frequency_knowledge
    → generate_faq_sop_candidate → store_promoted_memory
    """
    nodes = {}
    
    async def normalize_feedback(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        规范化反馈
        
        输入: feedback (from user)
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
        输出: feedback_class
        """
        feedback = state.normalized_feedback
        rating = feedback.get("rating", 0)
        
        if rating >= 4:
            feedback_class = "positive"
        elif rating <= 2:
            feedback_class = "negative"
        else:
            feedback_class = "neutral"
        
        return {
            "feedback_class": feedback_class,
            "action": "increase_interest" if feedback_class == "positive" else "decrease_interest",
        }
    
    async def build_profile_delta(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        构建画像增量
        
        输入: normalized_feedback, feedback_class
        输出: profile_delta
        """
        feedback = state.normalized_feedback
        
        delta = {
            "interests": [],
            "tags": [],
            "preferences": {},
            "activity": {
                "type": "feedback",
                "knowledge_id": feedback.get("knowledge_id"),
                "rating": feedback.get("rating"),
            },
        }
        
        if state.action == "decrease_interest":
            # 负反馈降低权重
            delta["remove_interests"] = [feedback.get("knowledge_id")]
        elif state.action == "increase_interest":
            # 正反馈增加兴趣
            delta["interests"] = [feedback.get("knowledge_id")]
        
        return {"profile_delta": delta}
    
    async def update_user_profile(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        更新用户画像
        
        输入: user_id, profile_delta
        输出: updated_profile
        """
        from knowledge_radar.services import ProfileService
        
        # Mock profile service
        class MockProfileRepo:
            async def get_by_user_id(self, uid):
                return {"user_id": uid, "interests": [], "tags": []}
            async def save(self, profile):
                pass
        
        service = ProfileService(MockProfileRepo())
        
        try:
            updated = await service.update_profile(
                user_id=state.user_id,
                updates=state.profile_delta,
            )
            
            return {
                "updated_profile": {
                    "user_id": updated.user_id,
                    "interests": updated.interests,
                    "tags": updated.tags,
                }
            }
        except:
            return {"updated_profile": {"user_id": state.user_id}}
    
    async def update_knowledge_usefulness(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        更新知识有用性
        
        输入: normalized_feedback, feedback_class
        输出: usefulness_update
        """
        return {
            "usefulness_update": {
                "knowledge_id": state.normalized_feedback.get("knowledge_id"),
                "new_score": 0.8 if state.feedback_class == "positive" else 0.3,
            }
        }
    
    async def detect_high_frequency_knowledge(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        检测高频知识
        
        输入: user_id
        输出: high_frequency_knowledge
        """
        # Mock: 检测被多次反馈的知识
        return {
            "high_frequency_knowledge": [
                {"knowledge_id": "k1", "access_count": 5, "avg_rating": 4.5}
            ]
        }
    
    async def generate_faq_sop_candidate(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        生成 FAQ/SOP 候选
        
        输入: high_frequency_knowledge
        输出: faq_sop_candidates
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.integrations import LLMClient
        import json
        
        prompt = load_prompt("faq_sop_promote")
        user_prompt = format_user_prompt(
            "faq_sop_promote",
            knowledge_items=json.dumps(state.high_frequency_knowledge, ensure_ascii=False),
            existing_faqs="[]",
            usage_patterns=json.dumps([
                {"knowledge_id": "k1", "access_count": 5, "users": ["u1", "u2"]}
            ], ensure_ascii=False),
        )
        
        llm = LLMClient()
        response = await llm.generate_text(
            prompt=user_prompt,
            system_prompt=prompt.get("system_prompt", ""),
        )
        
        try:
            data = json.loads(response)
        except:
            data = {"promote_candidates": []}
        
        return {"faq_sop_candidates": data.get("promote_candidates", [])}
    
    async def store_promoted_memory(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        存储提升的记忆
        
        输入: faq_sop_candidates
        输出: stored_memory
        """
        return {
            "stored_memory": {
                "promoted_count": len(state.faq_sop_candidates),
                "status": "completed",
            }
        }
    
    # 注册节点
    nodes["normalize_feedback"] = normalize_feedback
    nodes["classify_feedback"] = classify_feedback
    nodes["build_profile_delta"] = build_profile_delta
    nodes["update_user_profile"] = update_user_profile
    nodes["update_knowledge_usefulness"] = update_knowledge_usefulness
    nodes["detect_high_frequency_knowledge"] = detect_high_frequency_knowledge
    nodes["generate_faq_sop_candidate"] = generate_faq_sop_candidate
    nodes["store_promoted_memory"] = store_promoted_memory
    
    return nodes


async def run_feedback_memory_subgraph(state: KnowledgeRadarState) -> KnowledgeRadarState:
    """
    运行反馈记忆子图
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    nodes = build_feedback_memory_subgraph()
    
    execution_order = [
        "normalize_feedback",
        "classify_feedback",
        "build_profile_delta",
        "update_user_profile",
        "update_knowledge_usefulness",
        "detect_high_frequency_knowledge",
        "generate_faq_sop_candidate",
        "store_promoted_memory",
    ]
    
    for node_name in execution_order:
        if node_name not in nodes:
            continue
        
        try:
            result = await nodes[node_name](state)
            
            if isinstance(result, dict):
                for key, value in result.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
        
        except Exception as e:
            state.errors.append({
                "node": node_name,
                "error": str(e),
            })
    
    return state
