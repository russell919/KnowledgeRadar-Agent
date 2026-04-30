"""
Weekly Digest Subgraph - 每周摘要子图

生成每周知识摘要推送
"""

from typing import Dict, Any, Callable
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


def build_weekly_digest_subgraph() -> Dict[str, Callable]:
    """
    构建每周摘要子图
    
    流程：
    resolve_weekly_scope → build_weekly_time_window → collect_weekly_sources
    → extract_weekly_knowledge → build_theme_clusters → score_weekly_importance
    → load_weekly_user_profiles → plan_personalized_digest → generate_digest_card
    → push_decision_subgraph
    """
    nodes = {}
    
    async def resolve_weekly_scope(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        确定每周范围
        
        输入: scene_context
        输出: time_window (start, end)
        """
        from datetime import datetime, timedelta
        
        scene_context = state.scene_context or {}
        
        # 默认本周
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
        from knowledge_radar.services import RetrievalService
        
        # Mock 检索结果
        return {
            "retrieval_results": [
                {
                    "knowledge_id": "k1",
                    "title": "项目周会结论",
                    "summary": "讨论了本周进度和下周计划",
                    "source_refs": [{"source_type": "meeting"}],
                },
                {
                    "knowledge_id": "k2",
                    "title": "技术方案评审",
                    "summary": "确定了架构设计方向",
                    "source_refs": [{"source_type": "doc"}],
                },
            ]
        }
    
    async def extract_weekly_knowledge(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        抽取每周知识
        
        输入: retrieval_results
        输出: extracted_knowledge
        """
        return {
            "extracted_knowledge": state.retrieval_results
        }
    
    async def build_theme_clusters(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        构建主题聚类
        
        输入: extracted_knowledge, time_window
        输出: theme_clusters
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.integrations import LLMClient
        import json
        
        time_window = state.scene_context.get("time_window", {})
        
        prompt = load_prompt("weekly_theme_cluster")
        user_prompt = format_user_prompt(
            "weekly_theme_cluster",
            knowledge_items=json.dumps(state.extracted_knowledge[:10], ensure_ascii=False),
            time_range=json.dumps(time_window, ensure_ascii=False),
            min_cluster_size=2,
        )
        
        llm = LLMClient()
        response = await llm.generate_text(
            prompt=user_prompt,
            system_prompt=prompt.get("system_prompt", ""),
        )
        
        # 解析响应
        try:
            data = json.loads(response)
            themes = data.get("themes", [])
        except:
            # Fallback: 按类型聚类
            themes = [
                {
                    "theme_id": "theme_1",
                    "theme_title": "项目进展",
                    "summary": "本周项目相关讨论",
                    "knowledge_items": state.extracted_knowledge[:3],
                }
            ]
        
        return {"theme_clusters": themes}
    
    async def score_weekly_importance(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        评分每周重要性
        
        输入: extracted_knowledge
        输出: scored_knowledge
        """
        from knowledge_radar.services import ScoringService
        
        service = ScoringService()
        scored = service.score_weekly_importance(state.extracted_knowledge)
        
        return {"scored_knowledge": scored}
    
    async def load_weekly_user_profiles(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        加载用户画像
        
        输入: user_id
        输出: user_profiles
        """
        # Mock 用户画像
        return {
            "user_profiles": [
                {
                    "user_id": state.user_id,
                    "interests": ["项目进展", "技术方案"],
                    "tags": ["engineering"],
                    "preferences": {},
                }
            ]
        }
    
    async def plan_personalized_digest(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        规划个性化摘要
        
        输入: theme_clusters, user_profiles
        输出: personalized_plan
        """
        return {
            "personalized_plan": {
                "focus_themes": state.scene_context.get("theme_clusters", [])[:3],
                "excluded_items": [],
            }
        }
    
    async def generate_digest_card(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        生成摘要卡片
        
        输入: theme_clusters, user_profiles, personalized_plan
        输出: output_card
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.services import CardService
        from knowledge_radar.integrations import LLMClient
        import json
        
        prompt = load_prompt("weekly_digest_generate")
        user_prompt = format_user_prompt(
            "weekly_digest_generate",
            themes=json.dumps(state.scene_context.get("theme_clusters", []), ensure_ascii=False),
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
            data = {
                "card_title": "本周知识摘要",
                "summary": "本周知识摘要内容",
                "sections": [],
                "source_refs": [],
            }
        
        card_service = CardService()
        card = card_service.create_knowledge_card(
            knowledge_items=state.extracted_knowledge[:5],
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
    
    # 注册节点
    nodes["resolve_weekly_scope"] = resolve_weekly_scope
    nodes["build_weekly_time_window"] = build_weekly_time_window
    nodes["collect_weekly_sources"] = collect_weekly_sources
    nodes["extract_weekly_knowledge"] = extract_weekly_knowledge
    nodes["build_theme_clusters"] = build_theme_clusters
    nodes["score_weekly_importance"] = score_weekly_importance
    nodes["load_weekly_user_profiles"] = load_weekly_user_profiles
    nodes["plan_personalized_digest"] = plan_personalized_digest
    nodes["generate_digest_card"] = generate_digest_card
    
    return nodes


async def run_weekly_digest_subgraph(state: KnowledgeRadarState) -> KnowledgeRadarState:
    """
    运行每周摘要子图
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    nodes = build_weekly_digest_subgraph()
    
    execution_order = [
        "resolve_weekly_scope",
        "build_weekly_time_window",
        "collect_weekly_sources",
        "extract_weekly_knowledge",
        "build_theme_clusters",
        "score_weekly_importance",
        "load_weekly_user_profiles",
        "plan_personalized_digest",
        "generate_digest_card",
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
    
    # 调用推送决策子图
    from knowledge_radar.graph.subgraphs.push_decision import run_push_decision_subgraph
    state = await run_push_decision_subgraph(state)
    
    return state
