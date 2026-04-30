/**
 * 场景类型定义
 */
export type SceneType = 
  | 'weekly_digest'    // 每周知识推送
  | 'meeting_briefing'  // 会前简报
  | 'doc_change'        // 文档变更
  | 'onboarding'        // 新人入职/入组
  | 'manual';           // 手动触发

/**
 * 来源引用
 */
export interface SourceRef {
  type: 'document' | 'message' | 'meeting' | 'task' | 'base';
  id: string;
  title: string;
  url: string;
  updateTime?: string;
  author?: string;
}

/**
 * 运行场景输入
 */
export interface RunSceneInput {
  /** 场景类型 */
  sceneType: SceneType;
  /** 触发源ID（可选），如会议ID、文档ID等 */
  triggerId?: string;
  /** 工作空间ID（可选，默认使用配置的defaultWorkspaceId） */
  workspaceId?: string;
  /** 自定义参数（可选） */
  params?: Record<string, any>;
  /** 是否启用预览模式 */
  dryRun?: boolean;
}

/**
 * 运行场景输出
 */
export interface RunSceneOutput {
  /** 场景执行是否成功 */
  success: boolean;
  /** 场景执行ID，可用于后续查询 */
  executionId: string;
  /** 执行结果摘要 */
  summary: string;
  /** 推送内容预览（仅在dryRun模式下返回） */
  preview?: {
    title: string;
    content: string;
    receivers: string[];
    pushChannels: string[];
  };
  /** 推送统计 */
  stats?: {
    totalReceivers: number;
    successCount: number;
    failedCount: number;
  };
  /** 相关来源引用 */
  sourceRefs: SourceRef[];
  /** 错误信息（执行失败时返回） */
  error?: string;
}

/**
 * 事件摄入输入
 */
export interface IngestEventInput {
  /** 事件类型 */
  eventType: 'message' | 'document_updated' | 'document_created' | 'meeting_ended' | 'task_updated' | 'user_joined' | 'custom';
  /** 事件源ID */
  sourceId: string;
  /** 事件源类型 */
  sourceType: 'im' | 'doc' | 'calendar' | 'task' | 'base' | 'wiki' | 'mail';
  /** 事件数据 */
  data: Record<string, any>;
  /** 事件发生时间（ISO格式，默认当前时间） */
  eventTime?: string;
  /** 工作空间ID（可选） */
  workspaceId?: string;
}

/**
 * 事件摄入输出
 */
export interface IngestEventOutput {
  /** 摄入是否成功 */
  success: boolean;
  /** 事件ID */
  eventId: string;
  /** 处理状态 */
  status: 'pending' | 'processing' | 'completed' | 'failed';
  /** 处理结果描述 */
  message?: string;
  /** 错误信息（处理失败时返回） */
  error?: string;
}

/**
 * 反馈提交输入
 */
export interface SubmitFeedbackInput {
  /** 关联的执行ID */
  executionId: string;
  /** 反馈类型 */
  feedbackType: 'useful' | 'not_useful' | 'incorrect' | 'other';
  /** 反馈内容 */
  content: string;
  /** 用户ID */
  userId?: string;
  /** 额外参数 */
  metadata?: Record<string, any>;
}

/**
 * 反馈提交输出
 */
export interface SubmitFeedbackOutput {
  /** 反馈是否提交成功 */
  success: boolean;
  /** 反馈ID */
  feedbackId: string;
  /** 感谢信息 */
  message: string;
}

/**
 * 动作预览输入
 */
export interface PreviewActionInput {
  /** 动作类型 */
  actionType: 'push_content' | 'update_knowledge' | 'sync_data' | 'send_notification';
  /** 动作参数 */
  params: Record<string, any>;
  /** 工作空间ID（可选） */
  workspaceId?: string;
}

/**
 * 动作预览输出
 */
export interface PreviewActionOutput {
  /** 是否可以执行 */
  allowed: boolean;
  /** 预览内容 */
  preview: {
    title: string;
    description: string;
    impactScope: string;
    estimatedEffect: string;
    risks?: string[];
  };
  /** 确认后执行所需的参数 */
  executionParams?: Record<string, any>;
  /** 风险提示（如果有） */
  warnings?: string[];
}

/**
 * 管理同步输入
 */
export interface AdminSyncInput {
  /** 同步类型 */
  syncType: 'full' | 'incremental';
  /** 同步数据源 */
  sources?: ('im' | 'doc' | 'calendar' | 'task' | 'base' | 'wiki' | 'mail')[];
  /** 同步开始时间（ISO格式，仅增量同步时生效） */
  startTime?: string;
  /** 工作空间ID（可选） */
  workspaceId?: string;
  /** 是否异步执行 */
  async?: boolean;
}

/**
 * 管理同步输出
 */
export interface AdminSyncOutput {
  /** 同步是否启动成功 */
  success: boolean;
  /** 同步任务ID */
  taskId?: string;
  /** 同步状态 */
  status: 'queued' | 'running' | 'completed' | 'failed';
  /** 同步统计信息 */
  stats?: {
    totalItems: number;
    processedItems: number;
    failedItems: number;
    elapsedTime?: number;
  };
  /** 错误信息（同步失败时返回） */
  error?: string;
}
