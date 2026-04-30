"""
Knowledge Radar Agent - 场景运行路由
"""

import uuid
from datetime import datetime
from typing import Optional, List, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from knowledge_radar.config import get_settings
from knowledge_radar.logging_config import get_logger, add_log_context
from knowledge_radar.dependencies import get_agent_graph

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["scene"])


class SourceRef(BaseModel):
    """来源引用"""
    type: str = Field(description="来源类型: document | message | meeting | task | base")
    id: str = Field(description="来源ID")
    title: str = Field(description="来源标题")
    url: str = Field(description="来源URL")
    update_time: Optional[str] = None
    author: Optional[str] = None


class RunSceneRequest(BaseModel):
    """运行场景请求"""
    scene_type: str = Field(
        description="场景类型: weekly_digest | meeting_briefing | doc_change | onboarding | manual"
    )
    trigger_id: Optional[str] = Field(default=None, description="触发源ID")
    workspace_id: Optional[str] = Field(default=None, description="工作空间ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    params: Optional[dict] = Field(default=None, description="自定义参数")
    dry_run: bool = Field(default=False, description="预览模式，不实际执行推送")


class PreviewContent(BaseModel):
    """预览内容"""
    title: str
    content: str
    receivers: List[str]
    push_channels: List[str]


class PushStats(BaseModel):
    """推送统计"""
    total_receivers: int
    success_count: int
    failed_count: int


class RunSceneResponse(BaseModel):
    """运行场景响应"""
    success: bool
    execution_id: str
    summary: str
    status: str
    preview: Optional[PreviewContent] = None
    stats: Optional[PushStats] = None
    source_refs: List[SourceRef] = []
    error: Optional[str] = None


@router.post("/run-scene", response_model=RunSceneResponse)
async def run_scene(request: RunSceneRequest):
    """
    运行指定的知识雷达场景

    场景类型:
    - weekly_digest: 每周知识推送
    - meeting_briefing: 会前简报
    - doc_change: 文档变更提醒
    - onboarding: 新人入职引导
    - manual: 手动触发
    """
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"

    add_log_context(
        run_id=execution_id,
        scene_type=request.scene_type,
        user_id=request.user_id,
        workspace_id=request.workspace_id,
    )

    logger.info(f"Starting scene execution: {request.scene_type}")

    try:
        from knowledge_radar.graph.agent_graph import run_agent_graph, build_knowledge_radar_graph
        from knowledge_radar.graph.subgraphs.weekly_digest import run_weekly_digest_subgraph
        from knowledge_radar.graph.subgraphs.meeting_briefing import run_meeting_briefing_subgraph
        from knowledge_radar.graph.subgraphs.doc_change import run_doc_change_subgraph
        from knowledge_radar.graph.subgraphs.onboarding import run_onboarding_subgraph

        initial_state = {
            "trigger": {
                "trigger_type": request.scene_type,
                "user_id": request.user_id or "",
                "source_id": request.trigger_id or "",
                "content": request.params or {},
            },
            "user_id": request.user_id or "",
            "scene_context": request.params or {},
        }

        graph_runner = build_knowledge_radar_graph()

        scene_map = {
            "weekly_digest": run_weekly_digest_subgraph,
            "meeting_briefing": run_meeting_briefing_subgraph,
            "doc_change": run_doc_change_subgraph,
            "onboarding": run_onboarding_subgraph,
        }

        scene_func = scene_map.get(request.scene_type, run_weekly_digest_subgraph)

        state = await run_agent_graph(initial_state, graph_runner)

        scene_result = await scene_func(state)

        status = scene_result.status
        output_card = scene_result.output_card
        push_targets = scene_result.push_targets or []

        if status == "needs_preview" or request.dry_run:
            preview = PreviewContent(
                title=output_card.get("title", f"{request.scene_type} 场景推送") if output_card else "预览内容",
                content=output_card.get("summary", "预览内容占位") if output_card else "预览内容占位",
                receivers=push_targets[:5],
                push_channels=["feishu_im"],
            )
        else:
            preview = None

        summary = output_card.get("summary", f"场景 {request.scene_type} 执行完成") if output_card else f"场景 {request.scene_type} 执行完成"

        return RunSceneResponse(
            success=status != "failed",
            execution_id=execution_id,
            summary=summary,
            status=status,
            preview=preview,
            stats=PushStats(
                total_receivers=len(push_targets),
                success_count=len(push_targets) if status == "published" else 0,
                failed_count=0,
            ) if not request.dry_run else None,
            source_refs=[],
        )

    except Exception as e:
        logger.error(f"Scene execution failed: {str(e)}")
        return RunSceneResponse(
            success=False,
            execution_id=execution_id,
            summary=f"场景执行失败: {str(e)}",
            status="failed",
            error=str(e),
        )
