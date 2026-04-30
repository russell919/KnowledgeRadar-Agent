"""
Scene Router - 场景路由器

根据触发事件类型路由到对应的场景
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import json


@dataclass
class SceneContext:
    """
    场景上下文
    """
    scene: str
    scene_context: Dict[str, Any]
    confidence: float = 1.0
    reasoning: str = ""
    source_ref: Optional[Dict[str, Any]] = None


async def route_scene(
    trigger_type: str,
    trigger_data: Dict[str, Any],
    user_id: str,
) -> SceneContext:
    """
    路由场景
    
    根据 trigger.trigger_type 路由：
    - weekly_digest → weekly_digest
    - meeting_briefing → meeting_briefing
    - doc_change → doc_change
    - onboarding → onboarding
    - manual → 使用 scene_route prompt 判断
    
    Args:
        trigger_type: 触发类型
        trigger_data: 触发数据
        user_id: 用户ID
    
    Returns:
        SceneContext
    """
    # 直接映射
    scene_mapping = {
        "weekly_digest": "weekly_digest",
        "meeting_briefing": "meeting_briefing",
        "doc_change": "doc_change",
        "onboarding": "onboarding",
    }
    
    if trigger_type in scene_mapping:
        return SceneContext(
            scene=scene_mapping[trigger_type],
            scene_context=trigger_data,
            confidence=1.0,
            reasoning=f"Direct mapping from trigger_type: {trigger_type}",
            source_ref={
                "source_type": "trigger",
                "trigger_type": trigger_type,
            },
        )
    
    # 对于 manual 类型，使用 LLM 判断
    if trigger_type == "manual":
        return await _route_manual_trigger(trigger_data, user_id)
    
    # 未知类型，默认到 manual 处理
    return SceneContext(
        scene="manual",
        scene_context=trigger_data,
        confidence=0.5,
        reasoning=f"Unknown trigger_type: {trigger_type}, defaulting to manual",
        source_ref={"source_type": "trigger", "trigger_type": trigger_type},
    )


async def _route_manual_trigger(
    trigger_data: Dict[str, Any],
    user_id: str,
) -> SceneContext:
    """
    处理手动触发
    
    使用 scene_route prompt 判断场景类型
    
    Args:
        trigger_data: 触发数据
        user_id: 用户ID
    
    Returns:
        SceneContext
    """
    from knowledge_radar.prompts import load_prompt, format_user_prompt
    from knowledge_radar.integrations import LLMClient
    
    try:
        # 加载 prompt
        prompt = load_prompt("scene_route")
        
        # 格式化用户提示
        user_prompt = format_user_prompt(
            "scene_route",
            trigger_event=json.dumps(trigger_data, ensure_ascii=False),
            user_context=json.dumps({"user_id": user_id}, ensure_ascii=False),
        )
        
        # 调用 LLM
        client = LLMClient()
        
        class SceneRouteOutput:
            pass
        
        # 定义输出 schema
        class SceneRouteSchema:
            pass
        
        # 简化处理，直接使用文本生成
        response = await client.generate_text(
            prompt=user_prompt,
            system_prompt=prompt.get("system_prompt", ""),
        )
        
        # 解析 JSON 响应
        try:
            data = json.loads(response)
            return SceneContext(
                scene=data.get("recommended_scene", "other"),
                scene_context=trigger_data,
                confidence=data.get("confidence", 0.5),
                reasoning=data.get("reasoning", ""),
                source_ref={"source_type": "llm_routing"},
            )
        except json.JSONDecodeError:
            pass
        
    except Exception as e:
        pass
    
    # Fallback: 默认返回 weekly_digest
    return SceneContext(
        scene="weekly_digest",
        scene_context=trigger_data,
        confidence=0.3,
        reasoning="Failed to route, using default",
        source_ref={"source_type": "fallback"},
    )


def get_scene_entry_node(scene: str) -> str:
    """
    获取场景的入口节点名称
    
    Args:
        scene: 场景类型
    
    Returns:
        入口节点名称
    """
    entry_nodes = {
        "weekly_digest": "resolve_weekly_scope",
        "meeting_briefing": "read_meeting_event",
        "doc_change": "fetch_doc_versions",
        "onboarding": "resolve_new_member",
    }
    
    return entry_nodes.get(scene, "resolve_weekly_scope")
