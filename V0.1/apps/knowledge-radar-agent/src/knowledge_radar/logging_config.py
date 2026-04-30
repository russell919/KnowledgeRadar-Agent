"""
Knowledge Radar Agent 日志配置

使用 loguru 提供结构化日志支持，包含 run_id, scene_type, user_id 等上下文字段
"""

import sys
from contextvars import ContextVar
from typing import Optional

from loguru import logger

# 上下文变量，用于在日志中注入请求上下文
run_id_ctx: ContextVar[Optional[str]] = ContextVar("run_id", default=None)
scene_type_ctx: ContextVar[Optional[str]] = ContextVar("scene_type", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
workspace_id_ctx: ContextVar[Optional[str]] = ContextVar("workspace_id", default=None)


class LogContext:
    """日志上下文管理器"""
    
    def __init__(
        self,
        run_id: Optional[str] = None,
        scene_type: Optional[str] = None,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        self.run_id = run_id
        self.scene_type = scene_type
        self.user_id = user_id
        self.workspace_id = workspace_id
        self._tokens = []
    
    def __enter__(self):
        if self.run_id is not None:
            self._tokens.append(run_id_ctx.set(self.run_id))
        if self.scene_type is not None:
            self._tokens.append(scene_type_ctx.set(self.scene_type))
        if self.user_id is not None:
            self._tokens.append(user_id_ctx.set(self.user_id))
        if self.workspace_id is not None:
            self._tokens.append(workspace_id_ctx.set(self.workspace_id))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in self._tokens:
            # ContextVar不支持直接reset，需要重新设置
            pass
        self._tokens.clear()


def add_log_context(
    run_id: Optional[str] = None,
    scene_type: Optional[str] = None,
    user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
):
    """手动添加日志上下文"""
    if run_id is not None:
        run_id_ctx.set(run_id)
    if scene_type is not None:
        scene_type_ctx.set(scene_type)
    if user_id is not None:
        user_id_ctx.set(user_id)
    if workspace_id is not None:
        workspace_id_ctx.set(workspace_id)


def configure_logging(level: str = "INFO"):
    """
    配置 loguru 日志系统
    
    Args:
        level: 日志级别，默认 INFO
    """
    # 移除默认的 handler
    logger.remove()
    
    # 定义日志格式
    # 包含上下文变量的格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "{extra[run_id]:<36} | "
        "{extra[scene_type]:<20} | "
        "{extra[user_id]:<30} | "
        "<level>{message}</level>"
    )
    
    # 添加控制台输出
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # 添加文件输出（可选）
    # logger.add(
    #     "logs/knowledge_radar_{time}.log",
    #     rotation="00:00",
    #     retention="30 days",
    #     compression="zip",
    #     format=log_format,
    #     level=level,
    # )
    
    # 配置默认上下文
    logger.configure(
        extra={
            "run_id": "N/A",
            "scene_type": "N/A",
            "user_id": "N/A",
            "workspace_id": "N/A",
        }
    )


def get_logger(name: str = __name__):
    """
    获取带上下文信息的 logger
    
    Args:
        name: logger 名称
        
    Returns:
        配置好的 logger 实例
    """
    return logger.bind(name=name)
