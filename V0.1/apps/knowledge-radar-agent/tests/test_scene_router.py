"""
Test Scene Router - 测试场景路由
"""

import pytest
from knowledge_radar.graph.scene_router import route_scene, SceneContext


async def test_scene_router_weekly_digest():
    """测试 weekly_digest 场景"""
    result = await route_scene(
        trigger_type="weekly_digest",
        trigger_data={},
        user_id="test-user",
    )

    assert isinstance(result, SceneContext)
    assert result.scene == "weekly_digest"


async def test_scene_router_meeting_briefing():
    """测试 meeting_briefing 场景"""
    result = await route_scene(
        trigger_type="meeting_briefing",
        trigger_data={"meeting_id": "m001"},
        user_id="test-user",
    )

    assert result.scene == "meeting_briefing"


async def test_scene_router_doc_change():
    """测试 doc_change 场景"""
    result = await route_scene(
        trigger_type="doc_change",
        trigger_data={"doc_id": "d001"},
        user_id="test-user",
    )

    assert result.scene == "doc_change"


async def test_scene_router_onboarding():
    """测试 onboarding 场景"""
    result = await route_scene(
        trigger_type="onboarding",
        trigger_data={"new_user_id": "u001"},
        user_id="test-user",
    )

    assert result.scene == "onboarding"
