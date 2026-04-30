"""
Common Nodes - 通用节点

主图中使用的通用节点
"""

from typing import Dict, Any
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def normalize_trigger(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    规范化触发器
    
    输入: trigger 原始数据
    输出: trigger_type, user_id, source_type, source_id, raw_content
    
    节点处理逻辑：
    1. 从 trigger 中提取基本信息
    2. 设置默认值
    3. 返回规范化后的状态
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
    
    节点处理逻辑：
    1. 调用 OpenClawClient 获取用户上下文
    2. 提取用户的 ACL 标签
    3. 标记权限已检查
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
    
    节点处理逻辑：
    1. 根据 trigger_type 直接映射场景
    2. 对于 manual 类型，调用 LLM 判断
    3. 返回场景和上下文
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
    
    节点处理逻辑：
    1. 检查是否有 output_card
    2. 调用 SafetyService 检查安全性
    3. 根据检查结果设置状态
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
    
    节点处理逻辑：
    1. 如果 status=needs_preview，返回 needs_preview
    2. 如果需要广泛推送或关键变更，检查是否需要 human_preview
    3. 否则调用 CardService + OpenClawClient 发布
    """
    from knowledge_radar.services import CardService
    from knowledge_radar.integrations import OpenClawClient
    
    # 检查是否需要预览
    if state.status == "needs_preview":
        return {"status": "needs_preview"}
    
    # 检查是否需要人工预览
    output_card = state.output_card or {}
    is_wide_push = len(state.push_targets) > 5
    is_important_change = output_card.get("card_type") == "doc_change"
    
    if (is_wide_push or is_important_change) and state.scene_context.get("enable_human_preview"):
        return {"status": "needs_preview"}
    
    if not state.output_card:
        return {"status": "failed", "errors": ["No output card to publish"]}
    
    # 转换为飞书卡片
    card_service = CardService()
    output_card_obj = type("OutputCard", (), output_card)()
    feishu_card = card_service.to_feishu_card(output_card_obj)
    
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
    
    节点处理逻辑：
    1. 检查是否有反馈数据
    2. 调用 feedback_memory 子图处理
    """
    feedback = state.scene_context.get("feedback")
    
    if feedback:
        from knowledge_radar.graph.subgraphs.feedback_memory import run_feedback_memory_subgraph
        state = await run_feedback_memory_subgraph(state)
    
    return {"status": "completed"}
