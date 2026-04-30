"""
Knowledge Radar Subgraphs

场景子图集合
"""

from knowledge_radar.graph.subgraphs.weekly_digest import build_weekly_digest_subgraph
from knowledge_radar.graph.subgraphs.meeting_briefing import build_meeting_briefing_subgraph
from knowledge_radar.graph.subgraphs.doc_change import build_doc_change_subgraph
from knowledge_radar.graph.subgraphs.onboarding import build_onboarding_subgraph
from knowledge_radar.graph.subgraphs.knowledge_build import build_knowledge_build_subgraph
from knowledge_radar.graph.subgraphs.push_decision import build_push_decision_subgraph
from knowledge_radar.graph.subgraphs.feedback_memory import build_feedback_memory_subgraph

__all__ = [
    "build_weekly_digest_subgraph",
    "build_meeting_briefing_subgraph",
    "build_doc_change_subgraph",
    "build_onboarding_subgraph",
    "build_knowledge_build_subgraph",
    "build_push_decision_subgraph",
    "build_feedback_memory_subgraph",
]
