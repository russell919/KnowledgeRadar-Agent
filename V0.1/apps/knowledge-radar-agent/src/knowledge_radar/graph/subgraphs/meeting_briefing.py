"""
Meeting Briefing Subgraph - 会前简报子图

生成会前30分钟简报
"""

from typing import Dict, Any, Callable
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


def build_meeting_briefing_subgraph() -> Dict[str, Callable]:
    """
    构建会前简报子图
    
    流程：
    read_meeting_event → expand_meeting_topic → resolve_participant_context
    → plan_multi_source_retrieval → retrieve_previous_meetings → retrieve_related_docs
    → retrieve_open_tasks → retrieve_chat_episodes → retrieve_bitable_facts
    → rerank_meeting_context → generate_meeting_briefing
    """
    nodes = {}
    
    async def read_meeting_event(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        读取会议事件
        
        输入: scene_context (meeting_id)
        输出: meeting_info
        """
        from knowledge_radar.integrations import MockFeishuClient
        
        client = MockFeishuClient()
        meeting_id = state.scene_context.get("meeting_id", "")
        
        # Mock 会议数据
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
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.integrations import LLMClient
        import json
        
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
            data = {
                "expanded_topic": meeting_info.get("title", ""),
                "retrieval_keywords": ["项目", "进展", "计划"],
            }
        
        return {
            "expanded_topic": data.get("expanded_topic", ""),
            "retrieval_keywords": data.get("retrieval_keywords", []),
        }
    
    async def resolve_participant_context(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        解析参与人上下文
        
        输入: meeting_info
        输出: participant_contexts
        """
        meeting_info = state.scene_context.get("meeting_info", {})
        participants = meeting_info.get("participants", [])
        
        return {
            "participant_contexts": [
                {"user_id": p, "role": "participant"}
                for p in participants
            ]
        }
    
    async def plan_multi_source_retrieval(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        规划多来源检索
        
        输入: retrieval_keywords
        输出: retrieval_plan
        """
        return {
            "retrieval_plan": {
                "sources": ["previous_meetings", "related_docs", "open_tasks", "chat_episodes", "bitable_facts"],
                "keywords": state.retrieval_keywords if hasattr(state, "retrieval_keywords") else [],
            }
        }
    
    async def retrieve_previous_meetings(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        检索历史会议
        
        输入: retrieval_keywords
        输出: previous_meetings
        """
        return {
            "previous_meetings": [
                {
                    "meeting_id": "m1",
                    "title": "上次周会",
                    "summary": "确定了技术方案",
                    "source_refs": [],
                }
            ]
        }
    
    async def retrieve_related_docs(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        检索相关文档
        
        输入: retrieval_keywords
        输出: related_docs
        """
        return {
            "related_docs": [
                {
                    "doc_id": "d1",
                    "title": "技术方案文档",
                    "summary": "架构设计说明",
                    "source_refs": [],
                }
            ]
        }
    
    async def retrieve_open_tasks(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        检索开放任务
        
        输入: retrieval_keywords
        输出: open_tasks
        """
        return {
            "open_tasks": [
                {
                    "task_id": "t1",
                    "title": "完成技术方案",
                    "status": "进行中",
                    "owner": "user_1",
                    "source_refs": [],
                }
            ]
        }
    
    async def retrieve_chat_episodes(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        检索聊天片段
        
        输入: retrieval_keywords
        输出: chat_episodes
        """
        return {
            "chat_episodes": [
                {
                    "episode_id": "e1",
                    "summary": "讨论了项目进度",
                    "participants": ["user_1", "user_2"],
                    "source_refs": [],
                }
            ]
        }
    
    async def retrieve_bitable_facts(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        检索多维表格事实
        
        输入: retrieval_keywords
        输出: bitable_facts
        """
        return {
            "bitable_facts": [
                {
                    "fact": "项目进度80%",
                    "source": "进度表",
                    "source_refs": [],
                }
            ]
        }
    
    async def rerank_meeting_context(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        重排序会议上下文
        
        输入: previous_meetings, related_docs, open_tasks, chat_episodes, bitable_facts
        输出: ranked_context
        """
        all_context = (
            state.scene_context.get("previous_meetings", []) +
            state.scene_context.get("related_docs", []) +
            state.scene_context.get("open_tasks", []) +
            state.scene_context.get("chat_episodes", []) +
            state.scene_context.get("bitable_facts", [])
        )
        
        return {"ranked_context": all_context[:10]}
    
    async def generate_meeting_briefing(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        生成会议简报
        
        输入: meeting_info, expanded_topic, ranked_context, open_tasks, user_profile
        输出: output_card
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.services import CardService
        from knowledge_radar.integrations import LLMClient
        import json
        
        meeting_info = state.scene_context.get("meeting_info", {})
        ranked_context = state.scene_context.get("ranked_context", [])
        open_tasks = state.scene_context.get("open_tasks", [])
        
        prompt = load_prompt("meeting_briefing_generate")
        user_prompt = format_user_prompt(
            "meeting_briefing_generate",
            meeting_info=json.dumps({
                "expanded_topic": state.expanded_topic if hasattr(state, "expanded_topic") else "",
                "participants": meeting_info.get("participants", []),
            }, ensure_ascii=False),
            retrieved_knowledge=json.dumps(ranked_context, ensure_ascii=False),
            action_items=json.dumps(open_tasks, ensure_ascii=False),
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
            data = {
                "card_title": f"会前简报: {meeting_info.get('title', '')}",
                "meeting_summary": {},
                "relevant_background": [],
                "discussion_points": [],
            }
        
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
    
    # 注册节点
    nodes["read_meeting_event"] = read_meeting_event
    nodes["expand_meeting_topic"] = expand_meeting_topic
    nodes["resolve_participant_context"] = resolve_participant_context
    nodes["plan_multi_source_retrieval"] = plan_multi_source_retrieval
    nodes["retrieve_previous_meetings"] = retrieve_previous_meetings
    nodes["retrieve_related_docs"] = retrieve_related_docs
    nodes["retrieve_open_tasks"] = retrieve_open_tasks
    nodes["retrieve_chat_episodes"] = retrieve_chat_episodes
    nodes["retrieve_bitable_facts"] = retrieve_bitable_facts
    nodes["rerank_meeting_context"] = rerank_meeting_context
    nodes["generate_meeting_briefing"] = generate_meeting_briefing
    
    return nodes


async def run_meeting_briefing_subgraph(state: KnowledgeRadarState) -> KnowledgeRadarState:
    """
    运行会前简报子图
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    nodes = build_meeting_briefing_subgraph()
    
    execution_order = [
        "read_meeting_event",
        "expand_meeting_topic",
        "resolve_participant_context",
        "plan_multi_source_retrieval",
        "retrieve_previous_meetings",
        "retrieve_related_docs",
        "retrieve_open_tasks",
        "retrieve_chat_episodes",
        "retrieve_bitable_facts",
        "rerank_meeting_context",
        "generate_meeting_briefing",
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
