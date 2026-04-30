"""
Database Models - SQLAlchemy 2.0 Async Models

定义所有数据库表结构
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Float, Integer,
    ForeignKey, Index, JSON, Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from knowledge_radar.storage.db import Base


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


def utc_now():
    """获取当前 UTC 时间"""
    return datetime.utcnow()


# =============================================================================
# Source Objects - 来源对象
# =============================================================================

class SourceObjectModel(Base):
    """来源对象表"""
    __tablename__ = "source_objects"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    source_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    acl_tags: Mapped[list] = mapped_column(JSONB, default=list)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # 关系
    versions: Mapped[List["SourceObjectVersionModel"]] = relationship(
        "SourceObjectVersionModel",
        back_populates="source_object",
        cascade="all, delete-orphan"
    )
    chunks: Mapped[List["KnowledgeChunkModel"]] = relationship(
        "KnowledgeChunkModel",
        back_populates="source_object",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("ix_source_objects_type_workspace", "source_type", "workspace_id"),
        Index("ix_source_objects_acl", "acl_tags", postgresql_using="gin"),
    )


class SourceObjectVersionModel(Base):
    """来源对象版本表"""
    __tablename__ = "source_object_versions"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    source_object_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("source_objects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # 关系
    source_object: Mapped["SourceObjectModel"] = relationship(
        "SourceObjectModel",
        back_populates="versions"
    )
    
    __table_args__ = (
        Index("ix_source_version_object_version", "source_object_id", "version"),
    )


# =============================================================================
# Knowledge Items - 知识条目
# =============================================================================

class KnowledgeItemModel(Base):
    """知识条目表"""
    __tablename__ = "knowledge_items"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    knowledge_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    knowledge_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 关联信息（JSONB 存储列表）
    project_ids: Mapped[list] = mapped_column(JSONB, default=list)
    related_user_ids: Mapped[list] = mapped_column(JSONB, default=list)
    related_task_ids: Mapped[list] = mapped_column(JSONB, default=list)
    source_refs: Mapped[list] = mapped_column(JSONB, default=list)
    
    # 评分
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    authority_score: Mapped[float] = mapped_column(Float, default=0.5)
    
    # 状态
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # 关系
    chunks: Mapped[List["KnowledgeChunkModel"]] = relationship(
        "KnowledgeChunkModel",
        back_populates="knowledge_item",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("ix_knowledge_type_workspace", "knowledge_type", "workspace_id"),
        Index("ix_knowledge_status", "status"),
    )


class KnowledgeChunkModel(Base):
    """知识分块表（支持向量检索）"""
    __tablename__ = "knowledge_chunks"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    chunk_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    knowledge_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_object_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("source_objects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 向量嵌入 (pgvector)
    embedding: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # 全文搜索 (PostgreSQL TSVECTOR)
    text_search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR, nullable=True)
    
    # ACL 标签
    acl_tags: Mapped[list] = mapped_column(JSONB, default=list)
    
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # 关系
    knowledge_item: Mapped["KnowledgeItemModel"] = relationship(
        "KnowledgeItemModel",
        back_populates="chunks"
    )
    source_object: Mapped[Optional["SourceObjectModel"]] = relationship(
        "SourceObjectModel",
        back_populates="chunks"
    )
    
    __table_args__ = (
        Index("ix_chunk_knowledge", "knowledge_id"),
        Index("ix_chunk_text_search", "text_search_vector", postgresql_using="gin"),
    )


# =============================================================================
# Entity Relations - 实体关系
# =============================================================================

class EntityRelationModel(Base):
    """实体关系表"""
    __tablename__ = "entity_relations"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    target_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    relation_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    __table_args__ = (
        Index("ix_relation_source", "source_entity_type", "source_entity_id"),
        Index("ix_relation_target", "target_entity_type", "target_entity_id"),
        Index("ix_relation_type_workspace", "relation_type", "workspace_id"),
    )


# =============================================================================
# User Profiles - 用户画像
# =============================================================================

class UserProfileModel(Base):
    """用户画像表"""
    __tablename__ = "user_profiles"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # 标签体系
    role_tags: Mapped[list] = mapped_column(JSONB, default=list)
    project_tags: Mapped[list] = mapped_column(JSONB, default=list)
    topic_interest_tags: Mapped[list] = mapped_column(JSONB, default=list)
    negative_feedback_tags: Mapped[list] = mapped_column(JSONB, default=list)
    
    # 推送偏好
    push_preference: Mapped[dict] = mapped_column(JSONB, default=dict)
    muted_topics: Mapped[list] = mapped_column(JSONB, default=list)
    
    # 行为追踪
    recent_click_topics: Mapped[list] = mapped_column(JSONB, default=list)
    recent_click_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 活跃度
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 元数据
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    __table_args__ = (
        Index("ix_profile_user_workspace", "user_id", "workspace_id"),
    )


# =============================================================================
# Push Events - 推送事件
# =============================================================================

class PushEventModel(Base):
    """推送事件表"""
    __tablename__ = "push_events"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    push_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    execution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    scene_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 推送目标
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    group_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 推送内容
    knowledge_ids: Mapped[list] = mapped_column(JSONB, default=list)
    content_title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_summary: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 决策信息
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # push, skip, defer
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    
    # 推送状态
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, sent, failed, delivered
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 推送渠道
    push_channel: Mapped[str] = mapped_column(String(50), default="feishu_im")
    
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    __table_args__ = (
        Index("ix_push_execution", "execution_id"),
        Index("ix_push_user_status", "user_id", "status"),
        Index("ix_push_scene_status", "scene_type", "status"),
    )


# =============================================================================
# Feedback Events - 反馈事件
# =============================================================================

class FeedbackEventModel(Base):
    """反馈事件表"""
    __tablename__ = "feedback_events"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    feedback_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    push_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    execution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    
    knowledge_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 行为数据
    click_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    interaction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    __table_args__ = (
        Index("ix_feedback_push", "push_id"),
        Index("ix_feedback_user_type", "user_id", "feedback_type"),
    )


# =============================================================================
# Agent Runs - Agent 运行记录
# =============================================================================

class AgentRunModel(Base):
    """Agent 运行记录表"""
    __tablename__ = "agent_runs"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    scene_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 触发信息
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    operator_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 执行状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="running",
        index=True
    )  # running, completed, failed, cancelled
    
    # 输入输出摘要
    input_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # 统计
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    push_count: Mapped[int] = mapped_column(Integer, default=0)
    skip_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 执行时间
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 错误信息
    errors: Mapped[list] = mapped_column(JSONB, default=list)
    
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    
    __table_args__ = (
        Index("ix_run_scene_status", "scene_type", "status"),
        Index("ix_run_started", "started_at"),
    )


# =============================================================================
# Agent Checkpoints - Agent 检查点
# =============================================================================

class AgentCheckpointModel(Base):
    """Agent 检查点表（用于恢复）"""
    __tablename__ = "agent_checkpoints"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    run_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("agent_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    checkpoint_id: Mapped[str] = mapped_column(String(100), nullable=False)
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 状态快照
    state_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # 元数据
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    __table_args__ = (
        Index("ix_checkpoint_run_step", "run_id", "step_name"),
        Index("ix_checkpoint_created", "created_at"),
    )


# =============================================================================
# Scheduler Jobs - 调度任务
# =============================================================================

class SchedulerJobModel(Base):
    """调度任务表"""
    __tablename__ = "scheduler_jobs"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid
    )
    job_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    scene_type: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # 调度配置
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    schedule_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )  # cron, interval, one_time
    
    # 目标
    target_project_ids: Mapped[list] = mapped_column(JSONB, default=list)
    target_user_ids: Mapped[list] = mapped_column(JSONB, default=list)
    target_group_ids: Mapped[list] = mapped_column(JSONB, default=list)
    
    # 执行配置
    job_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # 状态
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled", index=True)
    
    # 执行记录
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    __table_args__ = (
        Index("ix_scheduler_job_type_enabled", "job_type", "is_enabled"),
        Index("ix_scheduler_next_run", "next_run_at"),
    )
