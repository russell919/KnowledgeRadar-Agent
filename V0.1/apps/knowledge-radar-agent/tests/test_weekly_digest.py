"""
Test Weekly Digest - 测试每周摘要
"""

import pytest
from knowledge_radar.graph.subgraphs.weekly_digest import (
    build_weekly_digest_subgraph,
    run_weekly_digest_subgraph,
)
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def test_weekly_digest_generation():
    """测试每周摘要生成"""
    state = KnowledgeRadarState(
        user_id="backend-apollo",
        scene_context={
            "workspace_id": "test-workspace",
            "theme_clusters": [
                {
                    "theme_id": "theme-001",
                    "theme_title": "项目进度",
                    "knowledge_items": [],
                }
            ],
        },
        user_profiles=[
            {
                "user_id": "backend-apollo",
                "interests": ["项目进度", "技术架构"],
            }
        ],
    )

    result = await run_weekly_digest_subgraph(state)

    assert result.status != "failed"
    assert result.output_card is not None


async def test_weekly_theme_clustering():
    """测试主题聚类"""
    from knowledge_radar.services import ScoringService

    service = ScoringService()
    knowledge_items = [
        {"title": "项目进度", "summary": "项目进展顺利"},
        {"title": "技术方案", "summary": "架构评审通过"},
    ]

    scored = service.score_weekly_importance(knowledge_items)
    assert len(scored) == len(knowledge_items)
