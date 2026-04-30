"""
Onboarding Nodes - 入职引导节点
"""

from typing import Dict, Any
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def resolve_new_member(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    解析新成员
    
    输入: scene_context (user_id)
    输出: new_member_info
    """
    return {
        "new_member_info": {
            "user_id": state.scene_context.get("user_id", state.user_id),
            "name": "新成员",
            "role": "engineer",
            "join_date": "2024-01-15",
        }
    }


async def analyze_knowledge_gap(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    分析知识差距
    
    输入: new_member_info, project_scope
    输出: gaps
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.integrations import LLMClient
    
    prompt = load_prompt("onboarding_gap_analyze")
    user_prompt = format_user_prompt(
        "onboarding_gap_analyze",
        user_profile=json.dumps(state.new_member_info, ensure_ascii=False),
        group_context=json.dumps(state.project_scope, ensure_ascii=False),
        retrieved_knowledge="[]",
    )
    
    llm = LLMClient()
    response = await llm.generate_text(
        prompt=user_prompt,
        system_prompt=prompt.get("system_prompt", ""),
    )
    
    try:
        data = json.loads(response)
    except:
        data = {"gaps": [{"gap_type": "project_knowledge", "title": "项目背景不熟悉", "priority": "high"}]}
    
    return {"gaps": data.get("gaps", [])}


async def generate_onboarding_pack(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    生成入职知识包
    
    输入: gaps, new_member_info, project_scope
    输出: output_card
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.services import CardService
    from knowledge_radar.integrations import LLMClient
    
    prompt = load_prompt("onboarding_pack_generate")
    user_prompt = format_user_prompt(
        "onboarding_pack_generate",
        gaps=json.dumps(state.gaps, ensure_ascii=False),
        user_profile=json.dumps(state.new_member_info, ensure_ascii=False),
        group_context=json.dumps(state.project_scope, ensure_ascii=False),
        retrieved_knowledge="[]",
    )
    
    llm = LLMClient()
    response = await llm.generate_text(
        prompt=user_prompt,
        system_prompt=prompt.get("system_prompt", ""),
    )
    
    try:
        data = json.loads(response)
    except:
        data = {"card_title": "新人入职指南"}
    
    return {
        "output_card": {
            "card_type": "onboarding",
            "title": data.get("card_title", "新人入职指南"),
            "summary": data.get("summary", ""),
            "content": json.dumps(data, ensure_ascii=False),
            "actions": [],
            "source_refs": data.get("source_refs", []),
        }
    }
