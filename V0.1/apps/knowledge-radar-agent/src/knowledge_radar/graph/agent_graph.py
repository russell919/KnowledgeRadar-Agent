"""
Agent Graph - 主图定义

LangGraph 风格的知识雷达 Agent 主图
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class KnowledgeRadarState:
    """
    Agent 状态
    
    所有节点共享的状态对象
    """
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 触发信息
    trigger: Optional[Dict[str, Any]] = None
    trigger_type: str = ""
    
    # 场景路由
    scene: str = ""
    scene_context: Optional[Dict[str, Any]] = None
    
    # 权限
    user_id: str = ""
    user_acl_tags: list = field(default_factory=list)
    permission_checked: bool = False
    
    # 知识构建
    source_type: str = ""
    source_id: str = ""
    raw_content: Dict[str, Any] = field(default_factory=dict)
    parsed_blocks: list = field(default_factory=list)
    extracted_knowledge: list = field(default_factory=list)
    linked_entities: list = field(default_factory=list)
    deduplicated_knowledge: list = field(default_factory=list)
    
    # 检索
    query: str = ""
    retrieval_results: list = field(default_factory=list)
    
    # 用户画像
    user_profiles: list = field(default_factory=list)
    target_user_id: str = ""
    
    # 输出
    output_card: Optional[Dict[str, Any]] = None
    push_targets: list = field(default_factory=list)
    push_explanations: list = field(default_factory=list)
    
    # 状态
    status: str = "pending"  # pending, running, needs_preview, completed, failed
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    checkpoint_id: Optional[str] = None


class GraphRunner:
    """
    图运行器
    
    提供 LangGraph 兼容的接口，如果 langgraph 不可用则使用 fallback
    """
    
    def __init__(self, use_fallback: bool = False):
        self.use_fallback = use_fallback
        self.graph = None
        self._nodes: Dict[str, Callable] = {}
        self._edges: list = []
        self._conditional_edges: Dict[str, Dict[str, str]] = {}
    
    def add_node(self, name: str, func: Callable):
        """添加节点"""
        self._nodes[name] = func
    
    def add_edge(self, from_node: str, to_node: str):
        """添加边"""
        self._edges.append((from_node, to_node))
    
    def add_conditional_edge(self, from_node: str, condition_func: Callable, mapping: Dict[str, str]):
        """添加条件边"""
        self._conditional_edges[from_node] = {"func": condition_func, "mapping": mapping}
    
    async def run(self, initial_state: Dict[str, Any]) -> KnowledgeRadarState:
        """
        运行图
        
        Args:
            initial_state: 初始状态
        
        Returns:
            最终状态
        """
        state = KnowledgeRadarState(**initial_state)
        
        # 简单的拓扑排序执行
        executed = set()
        queue = ["normalize_trigger"]
        
        while queue:
            node_name = queue.pop(0)
            
            if node_name in executed:
                continue
            
            if node_name not in self._nodes:
                continue
            
            # 执行节点
            node_func = self._nodes[node_name]
            
            try:
                result = await node_func(state)
                
                # 更新状态
                if isinstance(result, dict):
                    for key, value in result.items():
                        if hasattr(state, key):
                            setattr(state, key, value)
                
                executed.add(node_name)
                
                # 处理边
                for from_node, to_node in self._edges:
                    if from_node == node_name and to_node not in executed:
                        queue.append(to_node)
                
                # 处理条件边
                if node_name in self._conditional_edges:
                    cond = self._conditional_edges[node_name]
                    condition_result = cond["func"](state)
                    next_node = cond["mapping"].get(condition_result)
                    if next_node and next_node not in executed:
                        queue.append(next_node)
                
            except Exception as e:
                state.errors.append({
                    "node": node_name,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                state.status = "failed"
                break
        
        state.updated_at = datetime.utcnow().isoformat()
        return state


async def normalize_trigger(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    规范化触发器
    
    输入: trigger 原始数据
    输出: trigger_type, user_id, source_type, source_id
    """
    trigger = state.trigger or {}
    
    return {
        "trigger_type": trigger.get("trigger_type", "manual"),
        "user_id": trigger.get("user_id", ""),
        "source_type": trigger.get("source_type", ""),
        "source_id": trigger.get("source_id", ""),
        "raw_content": trigger.get("content", {}),
    }


async def resolve_permission(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    解析权限
    
    输入: user_id
    输出: user_acl_tags, permission_checked
    """
    from knowledge_radar.integrations import OpenClawClient
    
    client = OpenClawClient()
    context = await client.get_workspace_context(state.user_id)
    
    return {
        "user_acl_tags": context.get("acl_tags", []),
        "permission_checked": True,
    }


async def route_scene_node(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    路由场景
    
    输入: trigger_type, raw_content
    输出: scene, scene_context
    """
    from knowledge_radar.graph.scene_router import route_scene
    
    result = await route_scene(
        trigger_type=state.trigger_type,
        trigger_data=state.raw_content,
        user_id=state.user_id,
    )
    
    return {
        "scene": result.scene,
        "scene_context": result.scene_context,
    }


async def verify_output(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    验证输出
    
    输入: output_card
    输出: status
    """
    from knowledge_radar.services import SafetyService
    
    if not state.output_card:
        return {"status": "failed", "errors": ["No output card generated"]}
    
    safety = SafetyService()
    check_result = safety.check_output(
        output=state.output_card,
        user_id=state.user_id,
        user_acl_tags=state.user_acl_tags,
    )
    
    if not check_result["safe"]:
        return {
            "status": "failed",
            "errors": [f"Safety check failed: {check_result['checks']}"],
        }
    
    if check_result.get("requires_review"):
        return {"status": "needs_preview"}
    
    return {"status": "completed"}


async def publish_or_preview(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    发布或预览
    
    输入: output_card, push_targets, status
    输出: status
    """
    from knowledge_radar.services import CardService
    from knowledge_radar.integrations import OpenClawClient
    
    if state.status == "needs_preview":
        return {"status": "needs_preview"}
    
    if not state.output_card:
        return {"status": "failed", "errors": ["No output card to publish"]}
    
    # 转换为飞书卡片
    card_service = CardService()
    feishu_card = card_service.to_feishu_card(
        type("OutputCard", (), state.output_card)()
    )
    
    # 发布卡片
    client = OpenClawClient()
    
    for target in state.push_targets:
        await client.publish_card(
            card_payload=feishu_card.__dict__,
            recipients=[target],
            conversation_id=state.run_id,
        )
    
    return {"status": "published"}


async def feedback_memory_node(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    反馈记忆
    
    输入: 无（从之前状态获取）
    输出: status
    """
    # 反馈处理在 feedback_memory 子图中完成
    return {"status": "completed"}


def build_knowledge_radar_graph() -> GraphRunner:
    """
    构建知识雷达图
    
    主流程：
    normalize_trigger → resolve_permission → route_scene
    → (weekly_digest / meeting_briefing / doc_change / onboarding)
    → verify_output → publish_or_preview → feedback_memory
    """
    runner = GraphRunner(use_fallback=True)
    
    # 添加节点
    runner.add_node("normalize_trigger", normalize_trigger)
    runner.add_node("resolve_permission", resolve_permission)
    runner.add_node("route_scene", route_scene_node)
    runner.add_node("verify_output", verify_output)
    runner.add_node("publish_or_preview", publish_or_preview)
    runner.add_node("feedback_memory", feedback_memory_node)
    
    # 添加边
    runner.add_edge("normalize_trigger", "resolve_permission")
    runner.add_edge("resolve_permission", "route_scene")
    runner.add_edge("verify_output", "publish_or_preview")
    runner.add_edge("publish_or_preview", "feedback_memory")
    
    # 添加条件边 - 场景路由
    def scene_condition(state: KnowledgeRadarState) -> str:
        return state.scene
    
    runner.add_conditional_edge(
        "route_scene",
        scene_condition,
        {
            "weekly_digest": "weekly_digest_subgraph",
            "meeting_briefing": "meeting_briefing_subgraph",
            "doc_change": "doc_change_subgraph",
            "onboarding": "onboarding_subgraph",
        }
    )
    
    # 子图完成后回到 verify_output
    runner.add_edge("weekly_digest_subgraph", "verify_output")
    runner.add_edge("meeting_briefing_subgraph", "verify_output")
    runner.add_edge("doc_change_subgraph", "verify_output")
    runner.add_edge("onboarding_subgraph", "verify_output")
    
    return runner


async def run_agent_graph(
    initial_state: Dict[str, Any],
    graph_runner: Optional[GraphRunner] = None,
) -> KnowledgeRadarState:
    """
    运行知识雷达图
    
    Args:
        initial_state: 初始状态
        graph_runner: 图运行器（可选）
    
    Returns:
        最终状态
    """
    if graph_runner is None:
        graph_runner = build_knowledge_radar_graph()
    
    return await graph_runner.run(initial_state)
