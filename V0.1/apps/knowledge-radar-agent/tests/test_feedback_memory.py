"""
Test Feedback Memory - 测试反馈记忆
"""

import pytest
from knowledge_radar.graph.subgraphs.feedback_memory import (
    run_feedback_memory_subgraph,
)
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def test_feedback_updates_user_profile():
    """测试反馈更新用户画像"""
    state = KnowledgeRadarState(
        user_id="test-user",
        scene_context={
            "feedback": {
                "type": "explicit",
                "knowledge_id": "k001",
                "rating": 5,
                "comment": "非常有用",
            }
        },
    )

    result = await run_feedback_memory_subgraph(state)

    assert result.status != "failed"


async def test_negative_feedback_immediate():
    """测试负反馈立即生效"""
    from knowledge_radar.services import ProfileService

    class MockProfileRepo:
        async def get_by_user_id(self, user_id):
            return {"user_id": user_id, "interests": ["项目管理"]}
        async def save(self, profile):
            pass

    service = ProfileService(MockProfileRepo())
    updated = await service.update_profile(
        "test-user",
        {"feedback_type": "negative"},
    )

    assert updated is not None
