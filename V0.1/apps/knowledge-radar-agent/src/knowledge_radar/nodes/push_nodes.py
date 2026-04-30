"""
Push Nodes - 推送节点
"""

from typing import Dict, Any
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def hard_constraint_filter(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    硬约束过滤
    
    输入: push_targets, user_acl_tags
    输出: filtered_targets
    """
    from knowledge_radar.services import PermissionService
    
    service = PermissionService()
    items = [{"acl_tags": ["internal"], **t} for t in state.push_targets]
    filtered = service.filter_visible_items(state.user_id, items, state.user_acl_tags)
    
    return {"filtered_targets": [f.get("user_id", f.get("user_name")) for f in filtered]}


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
        scored = service.score_recipient_relevance(target, state.scene_context.get("extracted_knowledge", []))
        scores.append({"user_id": target, "relevance_score": scored[0].get("recipient_relevance_score", 0.5) if scored else 0.5})
    
    return {"recipient_scores": scores}


async def select_push_mode(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    选择推送模式
    
    输入: final_scores
    输出: push_mode, approved_targets
    """
    threshold = 0.4
    approved = [s for s in state.final_scores if s.get("final_score", 0) >= threshold]
    push_mode = "batch" if len(approved) > 10 else "personalized"
    
    return {"push_mode": push_mode, "approved_targets": approved}


async def generate_push_explanation(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    生成推送解释
    
    输入: output_card, approved_targets
    输出: push_explanations
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.integrations import LLMClient
    
    explanations = []
    
    for target in state.approved_targets[:3]:
        prompt = load_prompt("push_explanation_generate")
        user_prompt = format_user_prompt(
            "push_explanation_generate",
            knowledge_item=json.dumps(state.output_card or {}, ensure_ascii=False),
            user_profile=json.dumps({"user_id": target.get("user_id")}, ensure_ascii=False),
            push_reason=json.dumps({"relevance_score": target.get("final_score", 0.5)}, ensure_ascii=False),
        )
        
        llm = LLMClient()
        response = await llm.generate_text(prompt=user_prompt, system_prompt=prompt.get("system_prompt", ""))
        
        try:
            data = json.loads(response)
        except:
            data = {"explanation": "您可能感兴趣的更新", "reason": "内容相关"}
        
        explanations.append({
            "user_id": target.get("user_id"),
            "explanation": data.get("explanation", ""),
            "reason": data.get("reason", ""),
            "evidence_refs": data.get("evidence_refs", []),
        })
    
    return {"push_explanations": explanations}
