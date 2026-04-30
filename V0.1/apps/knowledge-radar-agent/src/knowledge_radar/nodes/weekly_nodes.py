"""
Weekly Nodes - 每周摘要节点
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def resolve_weekly_scope(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    确定每周范围
    
    输入: scene_context
    输出: time_window (start, end)
    """
    scene_context = state.scene_context or {}
    
    now = datetime.utcnow()
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=6)
    
    return {
        "time_window": {
            "start": scene_context.get("start", start.isoformat()),
            "end": scene_context.get("end", end.isoformat()),
        }
    }


async def build_weekly_time_window(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    构建时间窗口
    
    输入: time_window
    输出: query
    """
    time_window = state.scene_context.get("time_window", {})
    
    return {
        "query": f"时间范围: {time_window.get('start', '')} 至 {time_window.get('end', '')}"
    }


async def collect_weekly_sources(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    收集每周来源
    
    输入: query, user_acl_tags
    输出: retrieval_results
    """
    return {
        "retrieval_results": [
            {
                "knowledge_id": "k1",
                "title": "项目周会结论",
                "summary": "讨论了本周进度和下周计划",
                "source_refs": [{"source_type": "meeting"}],
            },
        ]
    }


async def build_theme_clusters(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    构建主题聚类
    
    输入: retrieval_results, time_window
    输出: theme_clusters
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.integrations import LLMClient
    
    time_window = state.scene_context.get("time_window", {})
    
    prompt = load_prompt("weekly_theme_cluster")
    user_prompt = format_user_prompt(
        "weekly_theme_cluster",
        knowledge_items=json.dumps(state.retrieval_results[:10], ensure_ascii=False),
        time_range=json.dumps(time_window, ensure_ascii=False),
        min_cluster_size=2,
    )
    
    llm = LLMClient()
    response = await llm.generate_text(
        prompt=user_prompt,
        system_prompt=prompt.get("system_prompt", ""),
    )
    
    try:
        data = json.loads(response)
        themes = data.get("themes", [])
    except:
        themes = [{"theme_id": "t1", "theme_title": "项目进展", "knowledge_items": state.retrieval_results[:3]}]
    
    return {"theme_clusters": themes}


async def score_weekly_importance(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    评分每周重要性
    
    输入: retrieval_results
    输出: scored_knowledge
    """
    from knowledge_radar.services import ScoringService
    
    service = ScoringService()
    scored = service.score_weekly_importance(state.retrieval_results)
    
    return {"scored_knowledge": scored}


async def generate_digest_card(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    生成摘要卡片
    
    输入: theme_clusters, user_profiles
    输出: output_card
    """
    import json
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.services import CardService
    from knowledge_radar.integrations import LLMClient
    
    prompt = load_prompt("weekly_digest_generate")
    user_prompt = format_user_prompt(
        "weekly_digest_generate",
        themes=json.dumps(state.theme_clusters, ensure_ascii=False),
        user_profile=json.dumps(state.user_profiles[0] if state.user_profiles else {}, ensure_ascii=False),
        time_range=json.dumps(state.scene_context.get("time_window", {}), ensure_ascii=False),
    )
    
    llm = LLMClient()
    response = await llm.generate_text(
        prompt=user_prompt,
        system_prompt=prompt.get("system_prompt", ""),
    )
    
    try:
        data = json.loads(response)
    except:
        data = {"card_title": "本周知识摘要", "summary": ""}
    
    card_service = CardService()
    card = card_service.create_knowledge_card(
        knowledge_items=state.retrieval_results[:5],
        card_type="summary",
    )
    
    return {
        "output_card": {
            "card_type": "summary",
            "title": data.get("card_title", "本周知识摘要"),
            "summary": data.get("summary", ""),
            "content": json.dumps(data, ensure_ascii=False),
            "actions": [],
            "source_refs": data.get("source_refs", []),
        }
    }
