"""
Knowledge Radar Agent - 健康检查路由
"""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["health"])

SERVICE_NAME = "knowledge-radar-agent"
SERVICE_VERSION = "1.0.0"


@router.get("/health")
async def health_check():
    """
    健康检查接口
    
    返回服务状态信息
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }
