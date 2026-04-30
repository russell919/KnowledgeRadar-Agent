"""
Push Decision Subgraph - 推送决策子图

决定是否推送、如何推送
"""

from typing import Dict, Any, Callable
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


def build_push_decision_subgraph() -> Dict[str, Callable]:
    """
    构建推送决策子图
    
    流程：
    hard_constraint_filter → score_recipient_relevance → score_content_relevance
    → adjust_by_user_profile → apply_anti_disturbance → select_push_mode
    → generate_push_explanation → assemble_card
    """
    nodes = {}
    
    async def hard_constraint_filter(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        硬约束过滤
        
        输入: push_targets, user_acl_tags
        输出: filtered_targets
        """
        from knowledge_radar.services import PermissionService
        
        service = PermissionService()
        
        items = [{"acl_tags": ["internal"], **t} for t in state.push_targets]
        filtered = service.filter_visible_items(
            user_id=state.user_id,
            items=items,
            user_acl_tags=state.user_acl_tags,
        )
        
        return {
            "filtered_targets": [f.get("user_id", f.get("user_name")) for f in filtered]
        }
    
    async def score_recipient_relevance(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        评分接收人相关性
        
        输入: filtered_targets, knowledge_items
        输出: recipient_scores
        """
        from knowledge_radar.services import ScoringService
        
        service = ScoringService()
        
        scores = []
        for target in state.filtered_targets:
            scored = service.score_recipient_relevance(
                recipient_id=target,
                knowledge_items=state.scene_context.get("extracted_knowledge", []),
            )
            scores.append({
                "user_id": target,
                "relevance_score": scored[0].get("recipient_relevance_score", 0.5) if scored else 0.5,
            })
        
        return {"recipient_scores": scores}
    
    async def score_content_relevance(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        评分内容相关性
        
        输入: knowledge_items, query
        输出: content_scores
        """
        from knowledge_radar.services import ScoringService
        
        service = ScoringService()
        
        query = state.scene_context.get("query", "")
        scored = service.score_content_relevance(
            query=query,
            knowledge_items=state.scene_context.get("extracted_knowledge", []),
        )
        
        return {
            "content_scores": [
                {"knowledge_id": s.get("knowledge_id"), "score": s.get("content_relevance_score")}
                for s in scored
            ]
        }
    
    async def adjust_by_user_profile(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        根据用户画像调整
        
        输入: recipient_scores, user_profiles
        输出: adjusted_scores
        """
        profiles = {p.get("user_id"): p for p in state.user_profiles}
        
        adjusted = []
        for score in state.recipient_scores:
            user_id = score.get("user_id")
            profile = profiles.get(user_id, {})
            
            interests = profile.get("interests", [])
            relevance = score.get("relevance_score", 0.5)
            
            # 兴趣匹配调整
            if interests:
                relevance += 0.1
            
            adjusted.append({**score, "adjusted_score": min(relevance, 1.0)})
        
        return {"adjusted_scores": adjusted}
    
    async def apply_anti_disturbance(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        应用打扰抑制
        
        输入: adjusted_scores, user_id
        输出: final_scores
        """
        from knowledge_radar.services import ScoringService
        
        service = ScoringService()
        
        final = []
        for score in state.adjusted_scores:
            penalty = service.score_anti_disturbance_penalty(
                recipient_id=score.get("user_id", ""),
                recent_pushes=0,  # Mock: 无近期推送
            )
            
            final_score = max(0, score.get("adjusted_score", 0.5) - penalty)
            final.append({**score, "final_score": final_score})
        
        return {"final_scores": final}
    
    async def select_push_mode(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        选择推送模式
        
        输入: final_scores, output_card
        输出: push_mode, approved_targets
        """
        threshold = 0.4
        
        approved = [s for s in state.final_scores if s.get("final_score", 0) >= threshold]
        
        if len(approved) > 10:
            push_mode = "batch"
        else:
            push_mode = "personalized"
        
        return {
            "push_mode": push_mode,
            "approved_targets": approved,
        }
    
    async def generate_push_explanation(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        生成推送解释
        
        输入: output_card, user_profile, push_reason
        输出: push_explanations
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.integrations import LLMClient
        import json
        
        explanations = []
        
        for target in state.approved_targets[:3]:
            prompt = load_prompt("push_explanation_generate")
            user_prompt = format_user_prompt(
                "push_explanation_generate",
                knowledge_item=json.dumps(state.output_card or {}, ensure_ascii=False),
                user_profile=json.dumps({"user_id": target.get("user_id")}, ensure_ascii=False),
                push_reason=json.dumps({
                    "relevance_score": target.get("final_score", 0.5),
                }, ensure_ascii=False),
            )
            
            llm = LLMClient()
            response = await llm.generate_text(
                prompt=user_prompt,
                system_prompt=prompt.get("system_prompt", ""),
            )
            
            try:
                data = json.loads(response)
            except:
                data = {"explanation": "这是您可能感兴趣的更新", "reason": "内容相关"}
            
            explanations.append({
                "user_id": target.get("user_id"),
                "explanation": data.get("explanation", ""),
                "reason": data.get("reason", ""),
                "evidence_refs": data.get("evidence_refs", []),
            })
        
        return {"push_explanations": explanations}
    
    async def assemble_card(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        组装卡片
        
        输入: output_card, push_explanations
        输出: final_output_card
        """
        return {
            "final_output_card": {
                **state.output_card,
                "push_explanations": state.push_explanations,
                "push_targets": [p.get("user_id") for p in state.approved_targets],
                "push_mode": state.push_mode,
            }
        }
    
    # 注册节点
    nodes["hard_constraint_filter"] = hard_constraint_filter
    nodes["score_recipient_relevance"] = score_recipient_relevance
    nodes["score_content_relevance"] = score_content_relevance
    nodes["adjust_by_user_profile"] = adjust_by_user_profile
    nodes["apply_anti_disturbance"] = apply_anti_disturbance
    nodes["select_push_mode"] = select_push_mode
    nodes["generate_push_explanation"] = generate_push_explanation
    nodes["assemble_card"] = assemble_card
    
    return nodes


async def run_push_decision_subgraph(state: KnowledgeRadarState) -> KnowledgeRadarState:
    """
    运行推送决策子图
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    nodes = build_push_decision_subgraph()
    
    execution_order = [
        "hard_constraint_filter",
        "score_recipient_relevance",
        "score_content_relevance",
        "adjust_by_user_profile",
        "apply_anti_disturbance",
        "select_push_mode",
        "generate_push_explanation",
        "assemble_card",
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
