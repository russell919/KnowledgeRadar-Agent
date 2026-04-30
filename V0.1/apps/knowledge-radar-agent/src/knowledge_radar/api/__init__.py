"""
Knowledge Radar Agent API 路由
"""

from knowledge_radar.api.routes_health import router as health_router
from knowledge_radar.api.routes_run import router as run_router
from knowledge_radar.api.routes_ingest import router as ingest_router
from knowledge_radar.api.routes_feedback import router as feedback_router
from knowledge_radar.api.routes_admin import router as admin_router

__all__ = [
    "health_router",
    "run_router",
    "ingest_router",
    "feedback_router",
    "admin_router",
]
