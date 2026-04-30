"""
Tasks - 后台任务定义
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List

from knowledge_radar.workers.celery_app import celery_app
from knowledge_radar.logging_config import get_logger, add_log_context
from knowledge_radar.graph.agent_graph import run_agent_graph, build_knowledge_radar_graph
from knowledge_radar.graph.subgraphs.weekly_digest import run_weekly_digest_subgraph
from knowledge_radar.services import IndexingService, ValidityService

logger = get_logger(__name__)


@celery_app.task(bind=True, name="knowledge_radar.workers.tasks.run_weekly_digest_task")
def run_weekly_digest_task(
    self,
    workspace_id: Optional[str] = None,
    user_ids: Optional[List[str]] = None,
):
    """
    执行每周知识摘要任务

    Args:
        workspace_id: 工作空间ID
        user_ids: 指定用户ID列表
    """
    execution_id = f"weekly_digest_{datetime.utcnow().strftime('%Y%m%d')}"
    add_log_context(run_id=execution_id, task_name="run_weekly_digest")

    logger.info(f"Starting weekly digest task, workspace: {workspace_id}")

    try:
        initial_state = {
            "trigger": {
                "trigger_type": "weekly_digest",
                "user_id": "system",
                "content": {
                    "workspace_id": workspace_id,
                    "user_ids": user_ids or [],
                },
            },
            "user_id": "system",
            "scene_context": {
                "workspace_id": workspace_id,
            },
        }

        graph_runner = build_knowledge_radar_graph()
        result = run_agent_graph(initial_state, graph_runner)

        logger.info(f"Weekly digest task completed")
        return {"status": "success", "execution_id": execution_id, "result": result}

    except Exception as e:
        logger.error(f"Weekly digest task failed: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name="knowledge_radar.workers.tasks.sync_workspace_sources_task")
def sync_workspace_sources_task(
    self,
    workspace_id: str,
    source_types: Optional[List[str]] = None,
    since: Optional[str] = None,
):
    """
    同步工作空间数据

    Args:
        workspace_id: 工作空间ID
        source_types: 来源类型，如 ["doc", "chat", "meeting"]
        since: 起始时间
    """
    execution_id = f"sync_{workspace_id}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    add_log_context(run_id=execution_id, task_name="sync_sources")

    logger.info(f"Starting sync task, workspace: {workspace_id}, types: {source_types}")

    try:
        # TODO: 调用 sync services 实际同步
        return {"status": "success", "execution_id": execution_id, "source_types": source_types}

    except Exception as e:
        logger.error(f"Sync task failed: {str(e)}")
        self.retry(exc=e, countdown=30, max_retries=5)


@celery_app.task(bind=True, name="knowledge_radar.workers.tasks.rebuild_indexes_task")
def rebuild_indexes_task(self, full_rebuild: bool = False):
    """
    重建索引

    Args:
        full_rebuild: 是否全量重建
    """
    execution_id = f"rebuild_indexes_{datetime.utcnow().strftime('%Y%m%d')}"
    add_log_context(run_id=execution_id, task_name="rebuild_indexes")

    logger.info(f"Starting rebuild indexes task, full_rebuild: {full_rebuild}")

    try:
        # TODO: 调用 indexing service 实际重建
        return {"status": "success", "execution_id": execution_id, "full_rebuild": full_rebuild}

    except Exception as e:
        logger.error(f"Rebuild indexes failed: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=2)


@celery_app.task(bind=True, name="knowledge_radar.workers.tasks.detect_high_frequency_knowledge_task")
def detect_high_frequency_knowledge_task(self):
    """检测高频知识"""
    execution_id = f"detect_hf_{datetime.utcnow().strftime('%Y%m%d')}"
    add_log_context(run_id=execution_id, task_name="detect_hf")

    logger.info("Starting detect high frequency knowledge")

    try:
        # TODO: 调用 feedback_memory subgraph
        return {"status": "success", "execution_id": execution_id}

    except Exception as e:
        logger.error(f"Detect HF knowledge failed: {str(e)}")
        self.retry(exc=e, countdown=120, max_retries=2)


@celery_app.task(bind=True, name="knowledge_radar.workers.tasks.expire_old_knowledge_task")
def expire_old_knowledge_task(self):
    """过期旧知识"""
    execution_id = f"expire_old_{datetime.utcnow().strftime('%Y%m%d')}"
    add_log_context(run_id=execution_id, task_name="expire_old")

    logger.info("Starting expire old knowledge task")

    try:
        from datetime import datetime, timedelta
        expire_before = datetime.utcnow() - timedelta(days=90)

        # TODO: 调用 validity service
        return {"status": "success", "execution_id": execution_id, "expire_before": expire_before}

    except Exception as e:
        logger.error(f"Expire old failed: {str(e)}")
        self.retry(exc=e, countdown=300, max_retries=1)
