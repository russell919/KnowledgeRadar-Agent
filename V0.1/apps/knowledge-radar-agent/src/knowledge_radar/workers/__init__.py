"""
Knowledge Radar Workers - 后台任务模块
"""

from knowledge_radar.workers.celery_app import celery_app

__all__ = ["celery_app"]
