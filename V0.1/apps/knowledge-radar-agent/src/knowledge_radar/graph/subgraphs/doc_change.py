"""
Doc Change Subgraph - 文档变更子图

处理文档变更通知
"""

from typing import Dict, Any, Callable
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


def build_doc_change_subgraph() -> Dict[str, Callable]:
    """
    构建文档变更子图
    
    流程：
    fetch_doc_versions → align_doc_structure → extract_change_units
    → classify_change_type → judge_change_importance
    → if not important → archive as digest/search_only
    → extract_affected_entities → resolve_impact_graph → build_recipient_candidates
    → retrieve_change_context → push_decision_scorer → generate_change_card
    """
    nodes = {}
    
    async def fetch_doc_versions(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        获取文档版本
        
        输入: scene_context (doc_id)
        输出: old_version, new_version
        """
        from knowledge_radar.integrations import MockFeishuClient
        
        client = MockFeishuClient()
        doc_id = state.scene_context.get("doc_id", "")
        
        # Mock 版本数据
        return {
            "old_version": {
                "version": "v1",
                "content": "# 项目计划\n\n## 目标\n完成开发",
                "updated_at": "2024-01-01",
            },
            "new_version": {
                "version": "v2",
                "content": "# 项目计划\n\n## 目标\n完成开发并上线",
                "updated_at": "2024-01-15",
            },
        }
    
    async def align_doc_structure(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        对齐文档结构
        
        输入: old_version, new_version
        输出: aligned_blocks
        """
        from knowledge_radar.services import DiffService
        
        service = DiffService()
        old_content = state.scene_context.get("old_version", {}).get("content", "")
        new_content = state.scene_context.get("new_version", {}).get("content", "")
        
        changes = service.compare_versions(
            {"content": old_content},
            {"content": new_content},
        )
        
        return {
            "aligned_blocks": [
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
    
    async def extract_change_units(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        抽取变更单元
        
        输入: aligned_blocks
        输出: change_units
        """
        return {"change_units": state.aligned_blocks}
    
    async def classify_change_type(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        分类变更类型
        
        输入: change_units
        输出: change_types
        """
        change_types = []
        
        for unit in state.change_units:
            change_types.append({
                "change_id": unit.get("change_id"),
                "type": unit.get("change_type"),
            })
        
        return {"change_types": change_types}
    
    async def judge_change_importance(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        判断变更重要性
        
        输入: change_units, doc_info, user_context
        输出: importance_level, push_recommendation
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.integrations import LLMClient
        import json
        
        prompt = load_prompt("doc_change_importance")
        user_prompt = format_user_prompt(
            "doc_change_importance",
            change_units=json.dumps(state.change_units[:5], ensure_ascii=False),
            doc_info=json.dumps({
                "doc_id": state.scene_context.get("doc_id", ""),
                "title": "项目文档",
            }, ensure_ascii=False),
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
            data = {
                "importance_level": "medium",
                "push_recommendation": "digest",
            }
        
        importance = data.get("importance_level", "low")
        
        return {
            "importance_level": importance,
            "push_recommendation": data.get("push_recommendation", "search_only"),
        }
    
    async def extract_affected_entities(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        抽取受影响实体
        
        输入: change_units
        输出: affected_entities
        """
        return {
            "affected_entities": [
                {"entity_id": "e1", "entity_type": "project", "name": "项目A"},
            ]
        }
    
    async def resolve_impact_graph(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        解析影响图
        
        输入: affected_entities
        输出: impact_graph
        """
        return {
            "impact_graph": {
                "nodes": state.affected_entities,
                "edges": [],
            }
        }
    
    async def build_recipient_candidates(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        构建候选接收人
        
        输入: affected_entities, doc_info
        输出: recipient_candidates
        """
        return {
            "recipient_candidates": [
                {
                    "user_id": "user_1",
                    "user_name": "张三",
                    "project_association": 0.8,
                    "task_ownership": 0.6,
                    "subscription": 0.9,
                }
            ]
        }
    
    async def retrieve_change_context(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        检索变更上下文
        
        输入: change_units
        输出: change_context
        """
        return {
            "change_context": state.change_units[:3]
        }
    
    async def push_decision_scorer(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        推送决策评分
        
        输入: recipient_candidates, change_context, user_profile
        输出: push_targets, scores
        """
        from knowledge_radar.services import ScoringService
        
        service = ScoringService()
        candidates = state.recipient_candidates
        
        scored = []
        for c in candidates:
            score = service.score_doc_change_push(
                change_units=state.change_units,
                recipient_id=c.get("user_id", ""),
                user_profile={},
            )
            scored.append({**c, "push_score": score})
        
        # 选择高评分接收人
        push_targets = [s["user_id"] for s in scored if s.get("push_score", 0) > 0.5]
        
        return {
            "push_targets": push_targets,
            "recipient_scores": scored,
        }
    
    async def generate_change_card(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        生成变更卡片
        
        输入: change_units, importance_level, recipient_info
        输出: output_card
        """
        from knowledge_radar.prompts import load_prompt, format_user_prompt
        from knowledge_radar.services import CardService
        from knowledge_radar.integrations import LLMClient
        import json
        
        prompt = load_prompt("doc_change_card_generate")
        user_prompt = format_user_prompt(
            "doc_change_card_generate",
            change_analysis=json.dumps({
                "importance_level": state.importance_level,
                "key_changes": state.change_units[:3],
                "affected_areas": ["项目进度"],
            }, ensure_ascii=False),
            diff_result=json.dumps(state.change_units, ensure_ascii=False),
            recipient_info=json.dumps({
                "user_id": state.target_user_id,
                "role": "participant",
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
            data = {
                "card_title": "文档变更通知",
                "summary": "文档已更新",
            }
        
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
    
    # 注册节点
    nodes["fetch_doc_versions"] = fetch_doc_versions
    nodes["align_doc_structure"] = align_doc_structure
    nodes["extract_change_units"] = extract_change_units
    nodes["classify_change_type"] = classify_change_type
    nodes["judge_change_importance"] = judge_change_importance
    nodes["extract_affected_entities"] = extract_affected_entities
    nodes["resolve_impact_graph"] = resolve_impact_graph
    nodes["build_recipient_candidates"] = build_recipient_candidates
    nodes["retrieve_change_context"] = retrieve_change_context
    nodes["push_decision_scorer"] = push_decision_scorer
    nodes["generate_change_card"] = generate_change_card
    
    return nodes


async def run_doc_change_subgraph(state: KnowledgeRadarState) -> KnowledgeRadarState:
    """
    运行文档变更子图
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    nodes = build_doc_change_subgraph()
    
    execution_order = [
        "fetch_doc_versions",
        "align_doc_structure",
        "extract_change_units",
        "classify_change_type",
        "judge_change_importance",
        "extract_affected_entities",
        "resolve_impact_graph",
        "build_recipient_candidates",
        "retrieve_change_context",
        "push_decision_scorer",
        "generate_change_card",
    ]
    
    for node_name in execution_order:
        if node_name not in nodes:
            continue
        
        try:
            result = await nodes[node_name](state)
            
            # 检查重要性
            if node_name == "judge_change_importance":
                if result.get("importance_level") == "low":
                    state.status = "archived"
                    break
            
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
    if state.status != "archived":
        from knowledge_radar.graph.subgraphs.push_decision import run_push_decision_subgraph
        state = await run_push_decision_subgraph(state)
    
    return state
