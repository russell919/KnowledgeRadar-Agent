"""
Knowledge Radar Agent - 反馈提交路由
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from knowledge_radar.logging_config import get_logger, add_log_context

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["feedback"])

# =============================================================================
# Request/Response Models
# =============================================================================

class SubmitFeedbackRequest(BaseModel):
    """反馈提交请求"""
    execution_id: str = Field(description="关联的执行ID")
    feedback_type: str = Field(
        description="反馈类型: useful | not_useful | incorrect | other"
    )
    content: str = Field(description="反馈内容")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    metadata: Optional[dict] = Field(default=None, description="额外元数据")


class SubmitFeedbackResponse(BaseModel):
    """反馈提交响应"""
    success: bool
    feedback_id: str
    message: str


# =============================================================================
# Routes
# =============================================================================

@router.post("/feedback", response_model=SubmitFeedbackResponse)
async def submit_feedback(request: SubmitFeedbackRequest):
    """
    提交用户对推送内容的反馈
    
    用于改进推送质量和更新用户画像
    """
    feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
    
    add_log_context(
        run_id=feedback_id,
        user_id=request.user_id,
    )
    
    logger.info(f"Received feedback for execution {request.execution_id}: {request.feedback_type}")
    
    try:
        # TODO_FEISHU_DOC_LOOKUP:
        # 确认反馈存储的具体方式
        # 确认用户画像的更新逻辑
        
        # 临时占位处理
        logger.warning("Using placeholder feedback handling - implement actual storage")
        
        return SubmitFeedbackResponse(
            success=True,
            feedback_id=feedback_id,
            message="感谢您的反馈，我们将持续改进",
        )
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
