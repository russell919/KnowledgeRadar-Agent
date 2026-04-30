"""
Celery App - Celery 应用初始化
"""

import os
from celery import Celery
from typing import Optional

from knowledge_radar.config import get_settings
from knowledge_radar.logging_config import get_logger

logger = get_logger(__name__)

settings = get_settings()


def create_celery_app() -> Celery:
    """创建并配置 Celery 应用"""
    broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    backend_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")

    app = Celery(
        "knowledge-radar",
        broker=broker_url,
        backend=backend_url,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5分钟
        task_soft_time_limit=240,  # 4分钟
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,
        task_default_retry_delay=60,
        task_max_retries=3,
    )

    app.conf.beat_schedule = {
        "run-weekly-digest": {
            "task": "knowledge_radar.workers.tasks.run_weekly_digest_task",
            "schedule": 60 * 60 * 24 * 7,  # 每周一次
        },
        "sync-workspace-sources": {
            "task": "knowledge_radar.workers.tasks.sync_workspace_sources_task",
            "schedule": 60 * 60,  # 每小时
        },
        "rebuild-indexes": {
            "task": "knowledge_radar.workers.tasks.rebuild_indexes_task",
            "schedule": 60 * 60 * 6,  # 每6小时
        },
        "detect-high-frequency": {
            "task": "knowledge_radar.workers.tasks.detect_high_frequency_knowledge_task",
            "schedule": 60 * 60 * 24,  # 每天
        },
        "expire-old-knowledge": {
            "task": "knowledge_radar.workers.tasks.expire_old_knowledge_task",
            "schedule": 60 * 60 * 24,  # 每天
        },
    }

    logger.info(f"Celery app created, broker: {broker_url}")
    return app


celery_app = create_celery_app()

celery_app.autodiscover_tasks(["knowledge_radar.workers"])
