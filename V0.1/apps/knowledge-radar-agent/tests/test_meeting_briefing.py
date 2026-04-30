"""
Test Meeting Briefing - 测试会前简报
"""

import pytest
from knowledge_radar.graph.subgraphs.meeting_briefing import (
    run_meeting_briefing_subgraph,
)
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def test_meeting_topic_expansion():
    """测试会议主题扩展"""
    from knowledge_radar.integrations import MockFeishuClient

    client = MockFeishuClient()
    meeting = await client.read_meeting_note("meeting-002")

    state = KnowledgeRadarState(
        user_id="pm-apollo",
        scene_context={
            "meeting_info": {
                "title": "周会",
                "description": "本周进度回顾",
                "participants": ["pm-apollo"],
            },
        },
    )

    result = await run_meeting_briefing_subgraph(state)

    assert result.status != "failed"


async def test_meeting_briefing_generation():
    """测试简报生成"""
    state = KnowledgeRadarState(
        user_id="test-user",
        scene_context={
            "meeting_info": {
                "title": "技术方案评审会",
                "participants": ["backend-apollo", "test-apollo"],
            },
            "retrieved_knowledge": [
                {
                    "title": "技术方案文档",
                    "summary": "技术方案评审要点",
                }
            ],
        },
    )

    result = await run_meeting_briefing_subgraph(state)

    assert result.status != "failed"
