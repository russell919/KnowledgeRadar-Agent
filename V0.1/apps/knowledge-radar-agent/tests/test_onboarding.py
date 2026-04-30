"""
Test Onboarding - 测试新人入组
"""

import pytest
from knowledge_radar.graph.subgraphs.onboarding import (
    run_onboarding_subgraph,
)
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def test_onboarding_pack_generation():
    """测试新人知识包生成"""
    state = KnowledgeRadarState(
        user_id="new-user",
        scene_context={
            "new_member_info": {
                "user_id": "new-user",
                "name": "赵小星",
                "role": "backend",
            },
            "project_scope": {
                "projects": [{"name": "Apollo"}],
            },
        },
    )

    result = await run_onboarding_subgraph(state)

    assert result.status != "failed"
    assert result.output_card is not None


async def test_knowledge_gap_analysis():
    """测试知识缺口分析"""
    from knowledge_radar.prompts import load_prompt

    prompt = load_prompt("onboarding_gap_analyze")
    assert "system_prompt" in prompt
