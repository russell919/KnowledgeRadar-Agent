"""
Onboarding Subgraph - 入职引导子图

生成新人入组知识包
"""

from typing import Dict, Any, Callable
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


def build_onboarding_subgraph() -> Dict[str, Callable]:
    """
    构建入职引导子图
    
    流程：
    resolve_new_member → resolve_project_scope → retrieve_project_memory
    → analyze_knowledge_gap → plan_onboarding_path → generate_onboarding_pack
    → mentor_preview if needed
    """
    nodes = {}
    
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
    
    async def resolve_project_scope(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        解析项目范围
        
        输入: new_member_info
        输出: project_scope
        """
        return {
            "project_scope": {
                "projects": [
                    {
                        "project_id": "p1",
                        "name": "知识雷达",
                        "description": "企业知识整合与分发系统",
                        "current_phase": "开发中",
                    }
                ],
                "team_members": [
                    {"user_id": "u1", "name": "张三", "role": "Tech Lead"},
                    {"user_id": "u2", "name": "李四", "role": "PM"},
                ],
            }
        }
    
    async def retrieve_project_memory(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        检索项目记忆
        
        输入: project_scope
        输出: project_knowledge
        """
        return {
            "project_knowledge": [
                {
                    "knowledge_id": "k1",
                    "title": "项目背景",
                    "summary": "企业知识分散，需要整合",
                    "source_refs": [],
                },
                {
                    "knowledge_id": "k2",
                    "title": "技术架构",
                    "summary": "基于 LangGraph 的 Agent 系统",
                    "source_refs": [],
                },
            ]
        }
    
    async def analyze_knowledge_gap(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        分析知识差距
        
        输入: new_member_info, project_scope, project_knowledge
        输出: gaps
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.integrations import LLMClient
        import json
        
        prompt = load_prompt("onboarding_gap_analyze")
        user_prompt = format_user_prompt(
            "onboarding_gap_analyze",
            user_profile=json.dumps(state.new_member_info, ensure_ascii=False),
            group_context=json.dumps(state.project_scope, ensure_ascii=False),
            retrieved_knowledge=json.dumps(state.project_knowledge, ensure_ascii=False),
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
                "gaps": [
                    {
                        "gap_type": "project_knowledge",
                        "title": "项目背景不熟悉",
                        "priority": "high",
                    }
                ]
            }
        
        return {"gaps": data.get("gaps", [])}
    
    async def plan_onboarding_path(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        规划入职路径
        
        输入: gaps, project_scope
        输出: onboarding_path
        """
        high_priority_gaps = [g for g in state.gaps if g.get("priority") == "high"]
        
        return {
            "onboarding_path": {
                "phases": [
                    {"week": 1, "focus": "项目背景和技术架构", "gaps": high_priority_gaps[:2]},
                    {"week": 2, "focus": "团队协作和工作流程", "gaps": []},
                ]
            }
        }
    
    async def generate_onboarding_pack(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        生成入职知识包
        
        输入: gaps, new_member_info, project_scope, project_knowledge, onboarding_path
        输出: output_card
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.services import CardService
        from knowledge_radar.integrations import LLMClient
        import json
        
        prompt = load_prompt("onboarding_pack_generate")
        user_prompt = format_user_prompt(
            "onboarding_pack_generate",
            gaps=json.dumps(state.gaps, ensure_ascii=False),
            user_profile=json.dumps(state.new_member_info, ensure_ascii=False),
            group_context=json.dumps(state.project_scope, ensure_ascii=False),
            retrieved_knowledge=json.dumps(state.project_knowledge, ensure_ascii=False),
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
                "card_title": "新人入职指南",
                "overview": {"project_summary": "知识雷达项目"},
                "must_read_materials": [],
            }
        
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
    
    async def mentor_preview(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        导师预览
        
        输入: output_card
        输出: preview_status
        """
        # 如果需要人工预览
        return {"preview_status": "pending_mentor_review"}
    
    # 注册节点
    nodes["resolve_new_member"] = resolve_new_member
    nodes["resolve_project_scope"] = resolve_project_scope
    nodes["retrieve_project_memory"] = retrieve_project_memory
    nodes["analyze_knowledge_gap"] = analyze_knowledge_gap
    nodes["plan_onboarding_path"] = plan_onboarding_path
    nodes["generate_onboarding_pack"] = generate_onboarding_pack
    nodes["mentor_preview"] = mentor_preview
    
    return nodes


async def run_onboarding_subgraph(state: KnowledgeRadarState) -> KnowledgeRadarState:
    """
    运行入职引导子图
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    nodes = build_onboarding_subgraph()
    
    execution_order = [
        "resolve_new_member",
        "resolve_project_scope",
        "retrieve_project_memory",
        "analyze_knowledge_gap",
        "plan_onboarding_path",
        "generate_onboarding_pack",
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
