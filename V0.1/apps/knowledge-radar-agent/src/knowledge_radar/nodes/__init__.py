"""
Knowledge Radar Nodes

各个场景的节点集合
"""

from knowledge_radar.nodes.common import (
    normalize_trigger,
    resolve_permission,
    route_scene_node,
    verify_output,
    publish_or_preview,
    feedback_memory_node,
)
from knowledge_radar.nodes.weekly_nodes import (
    resolve_weekly_scope,
    build_weekly_time_window,
    collect_weekly_sources,
    build_theme_clusters,
    score_weekly_importance,
    generate_digest_card,
)
from knowledge_radar.nodes.meeting_nodes import (
    read_meeting_event,
    expand_meeting_topic,
    retrieve_previous_meetings,
    generate_meeting_briefing,
)
from knowledge_radar.nodes.doc_change_nodes import (
    fetch_doc_versions,
    extract_change_units,
    judge_change_importance,
    generate_change_card,
)
from knowledge_radar.nodes.onboarding_nodes import (
    resolve_new_member,
    analyze_knowledge_gap,
    generate_onboarding_pack,
)
from knowledge_radar.nodes.push_nodes import (
    hard_constraint_filter,
    score_recipient_relevance,
    select_push_mode,
    generate_push_explanation,
)
from knowledge_radar.nodes.feedback_nodes import (
    normalize_feedback,
    classify_feedback,
    update_user_profile,
)

__all__ = [
    # Common
    "normalize_trigger",
    "resolve_permission",
    "route_scene_node",
    "verify_output",
    "publish_or_preview",
    "feedback_memory_node",
    # Weekly
    "resolve_weekly_scope",
    "build_weekly_time_window",
    "collect_weekly_sources",
    "build_theme_clusters",
    "score_weekly_importance",
    "generate_digest_card",
    # Meeting
    "read_meeting_event",
    "expand_meeting_topic",
    "retrieve_previous_meetings",
    "generate_meeting_briefing",
    # Doc Change
    "fetch_doc_versions",
    "extract_change_units",
    "judge_change_importance",
    "generate_change_card",
    # Onboarding
    "resolve_new_member",
    "analyze_knowledge_gap",
    "generate_onboarding_pack",
    # Push
    "hard_constraint_filter",
    "score_recipient_relevance",
    "select_push_mode",
    "generate_push_explanation",
    # Feedback
    "normalize_feedback",
    "classify_feedback",
    "update_user_profile",
]
