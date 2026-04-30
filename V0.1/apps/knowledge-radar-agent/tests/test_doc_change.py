"""
Test Doc Change - 测试文档变更
"""

import pytest
from knowledge_radar.graph.subgraphs.doc_change import (
    run_doc_change_subgraph,
)
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def test_doc_change_importance_judgement():
    """测试重要性判断"""
    from knowledge_radar.services import ScoringService
    from knowledge_radar.services import DocParserService

    old_version = {"content": "M3 上线时间：6月1日"}
    new_version = {"content": "M3 上线时间：6月15日"}

    state = KnowledgeRadarState(
        user_id="test-user",
        scene_context={
            "old_version": old_version,
            "new_version": new_version,
        },
    )

    result = await run_doc_change_subgraph(state)

    assert result.status != "failed"


async def test_change_impact_and_recipient_candidates():
    """测试影响分析和候选接收人"""
    from knowledge_radar.services import ImpactService

    class MockRepo:
        pass

    service = ImpactService(MockRepo(), MockRepo())

    entities = await service.find_impacted_entities(
        change_units=[],
        project_ids=["apollo-project"],
    )

    recipients = await service.find_candidate_recipients(
        change_units=[],
        project_ids=["apollo-project"],
    )

    assert isinstance(recipients, list)
