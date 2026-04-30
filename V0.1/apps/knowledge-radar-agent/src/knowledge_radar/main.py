"""
Knowledge Radar Agent - FastAPI 应用入口

企业知识整合与分发服务的 HTTP API
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from knowledge_radar import __version__
from knowledge_radar.config import get_settings
from knowledge_radar.logging_config import configure_logging, get_logger
from knowledge_radar.api import (
    health_router,
    run_router,
    ingest_router,
    feedback_router,
    admin_router,
)

# 初始化日志
settings = get_settings()
configure_logging(level=settings.service.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 60)
    logger.info(f"Knowledge Radar Agent v{__version__} starting...")
    logger.info(f"Log level: {settings.service.LOG_LEVEL}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'N/A'}")
    logger.info("=" * 60)
    
    yield
    
    # 关闭时
    logger.info("Knowledge Radar Agent shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title="Knowledge Radar Agent",
    description="企业知识整合与分发服务 - 提供知识推送、会前简报、文档变更提醒、新人入职引导等场景支持",
    version=__version__,
    docs_url="/docs" if settings.service.LOG_LEVEL == "DEBUG" else None,
    redoc_url="/redoc" if settings.service.LOG_LEVEL == "DEBUG" else None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.service.ALLOWED_ORIGINS.split(",") if hasattr(settings.service, 'ALLOWED_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(health_router)
app.include_router(run_router)
app.include_router(ingest_router)
app.include_router(feedback_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "knowledge-radar-agent",
        "version": __version__,
        "docs": "/docs" if settings.service.LOG_LEVEL == "DEBUG" else "disabled",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return ORJSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )
