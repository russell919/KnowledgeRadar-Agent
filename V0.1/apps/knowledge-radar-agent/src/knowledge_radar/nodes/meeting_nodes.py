"""
Meeting Nodes - 会议节点
"""

from typing import Dict, Any
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def read_meeting_event(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    读取会议事件
    
    输入: scene_context (meeting_id)
    输出: meeting_info
    """
    from knowledge_radar.integrations import MockFeishuClient
    
    client = MockFeishuClient()
    meeting_id = state.scene_context.get("meeting_id", "")
    
    meeting_info = {
        "meeting_id": meeting_id,
        "title": "项目周会",
        "description": "讨论本周进展",
        "participants": ["user_1", "user_2", "user_3"],
        "start_time": "2024-01-15T10:00:00Z",
    }
    
    return {"meeting_info": meeting_info}


async def expand_meeting_topic(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    扩展会议主题
    
    输入: meeting_info
    输出: expanded_topic, retrieval_keywords
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.integrations import LLMClient
    
    meeting_info = state.scene_context.get("meeting_info", {})
    
    prompt = load_prompt("meeting_topic_expand")
    user_prompt = format_user_prompt(
        "meeting_topic_expand",
        meeting_basic_info=json.dumps(meeting_info, ensure_ascii=False),
        recent_project_events="[]",
        known_context="{}",
    )
    
    llm = LLMClient()
    response = await llm.generate_text(
        prompt=user_prompt,
        system_prompt=prompt.get("system_prompt", ""),
    )
    
    try:
        data = json.loads(response)
    except:
        data = {"expanded_topic": meeting_info.get("title", ""), "retrieval_keywords": ["项目"]}
    
    return {
        "expanded_topic": data.get("expanded_topic", ""),
        "retrieval_keywords": data.get("retrieval_keywords", []),
    }


async def retrieve_previous_meetings(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    检索历史会议
    
    输入: retrieval_keywords
    输出: previous_meetings
    """
    return {
        "previous_meetings": [
            {"meeting_id": "m1", "title": "上次周会", "summary": "确定了技术方案", "source_refs": []}
        ]
    }


async def generate_meeting_briefing(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    生成会议简报
    
    输入: meeting_info, expanded_topic, ranked_context
    输出: output_card
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.services import CardService
    from knowledge_radar.integrations import LLMClient
    
    meeting_info = state.scene_context.get("meeting_info", {})
    
    prompt = load_prompt("meeting_briefing_generate")
    user_prompt = format_user_prompt(
        "meeting_briefing_generate",
        meeting_info=json.dumps({"expanded_topic": state.expanded_topic, "participants": meeting_info.get("participants", [])}, ensure_ascii=False),
        retrieved_knowledge=json.dumps(state.scene_context.get("ranked_context", []), ensure_ascii=False),
        action_items="[]",
        user_profile=json.dumps(state.user_profiles[0] if state.user_profiles else {}, ensure_ascii=False),
    )
    
    llm = LLMClient()
    response = await llm.generate_text(
        prompt=user_prompt,
        system_prompt=prompt.get("system_prompt", ""),
    )
    
    try:
        data = json.loads(response)
    except:
        data = {"card_title": f"会前简报: {meeting_info.get('title', '')}"}
    
    return {
        "output_card": {
            "card_type": "meeting_briefing",
            "title": data.get("card_title", "会前简报"),
            "summary": data.get("summary", ""),
            "content": json.dumps(data, ensure_ascii=False),
            "actions": [],
            "source_refs": data.get("source_refs", []),
        }
    }
