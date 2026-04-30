"""
Test Push Decision - 测试推送决策
"""

import pytest
from knowledge_radar.graph.subgraphs.push_decision import (
    run_push_decision_subgraph,
)
from knowledge_radar.graph.agent_graph import KnowledgeRadarState
from knowledge_radar.services import PermissionService


async def test_acl_filtering():
    """测试 ACL 权限过滤"""
    service = PermissionService()
    items = [
        {"acl_tags": ["internal"], "title": "测试1"},
        {"acl_tags": ["private"], "title": "测试2"},
    ]
    user_tags = ["internal"]

    filtered = service.filter_visible_items("test-user", items, user_tags)

    assert len(filtered) == 1


async def test_anti_disturbance():
    """测试反打扰机制"""
    from knowledge_radar.services import ScoringService

    service = ScoringService()
    penalty = service.score_anti_disturbance_penalty("test-user", recent_pushes=10)

    assert penalty > 0


async def test_push_decision_with_profile():
    """测试推送决策（带画像影响）"""
    state = KnowledgeRadarState(
        user_id="test-user",
        push_targets=[
            {"user_id": "user-1", "score": 0.8},
            {"user_id": "user-2", "score": 0.3},
        ],
        user_profiles=[
            {
                "user_id": "user-1",
                "interests": ["项目进度"],
            }
        ],
    )

    result = await run_push_decision_subgraph(state)

    assert result.status != "failed"
