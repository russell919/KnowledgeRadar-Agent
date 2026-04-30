"""
Doc Change Nodes - 文档变更节点
"""

from typing import Dict, Any
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def fetch_doc_versions(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    获取文档版本
    
    输入: scene_context (doc_id)
    输出: old_version, new_version
    """
    return {
        "old_version": {"version": "v1", "content": "# 项目计划\n\n## 目标\n完成开发", "updated_at": "2024-01-01"},
        "new_version": {"version": "v2", "content": "# 项目计划\n\n## 目标\n完成开发并上线", "updated_at": "2024-01-15"},
    }


async def extract_change_units(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    抽取变更单元
    
    输入: old_version, new_version
    输出: change_units
    """
    from knowledge_radar.services import DiffService
    
    service = DiffService()
    changes = service.compare_versions(state.old_version, state.new_version)
    
    return {
        "change_units": [
            {
                "change_id": c.change_id,
                "change_type": c.change_type,
                "section_path": c.section_path,
                "old_content": c.old_content,
                "new_content": c.new_content,
            }
            for c in changes
        ]
    }


async def judge_change_importance(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    判断变更重要性
    
    输入: change_units, doc_info
    输出: importance_level, push_recommendation
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.integrations import LLMClient
    
    prompt = load_prompt("doc_change_importance")
    user_prompt = format_user_prompt(
        "doc_change_importance",
        change_units=json.dumps(state.change_units[:5], ensure_ascii=False),
        doc_info=json.dumps({"doc_id": state.scene_context.get("doc_id", ""), "title": "项目文档"}, ensure_ascii=False),
        user_context=json.dumps({"user_id": state.user_id}, ensure_ascii=False),
    )
    
    llm = LLMClient()
    response = await llm.generate_text(
        prompt=user_prompt,
        system_prompt=prompt.get("system_prompt", ""),
    )
    
    try:
        data = json.loads(response)
    except:
        data = {"importance_level": "medium", "push_recommendation": "digest"}
    
    return {
        "importance_level": data.get("importance_level", "low"),
        "push_recommendation": data.get("push_recommendation", "search_only"),
    }


async def generate_change_card(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    生成变更卡片
    
    输入: change_units, importance_level
    输出: output_card
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.services import CardService
    from knowledge_radar.integrations import LLMClient
    
    prompt = load_prompt("doc_change_card_generate")
    user_prompt = format_user_prompt(
        "doc_change_card_generate",
        change_analysis=json.dumps({"importance_level": state.importance_level, "key_changes": state.change_units[:3]}, ensure_ascii=False),
        diff_result=json.dumps(state.change_units, ensure_ascii=False),
        recipient_info=json.dumps({"user_id": state.target_user_id}, ensure_ascii=False),
    )
    
    llm = LLMClient()
    response = await llm.generate_text(
        prompt=user_prompt,
        system_prompt=prompt.get("system_prompt", ""),
    )
    
    try:
        data = json.loads(response)
    except:
        data = {"card_title": "文档变更通知", "summary": "文档已更新"}
    
    return {
        "output_card": {
            "card_type": "doc_change",
            "title": data.get("card_title", "文档变更通知"),
            "summary": data.get("summary", ""),
            "content": json.dumps(data, ensure_ascii=False),
            "actions": [],
            "source_refs": data.get("source_refs", []),
        }
    }
