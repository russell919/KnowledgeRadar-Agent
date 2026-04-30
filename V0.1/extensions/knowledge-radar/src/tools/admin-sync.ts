import type { HttpClient } from '../http-client';
import type { KnowledgeRadarConfig } from '../config';
import type { AdminSyncInput, AdminSyncOutput } from '../types';

interface ToolRegistry {
  registerTool: <Input, Output>(tool: ToolDefinition<Input, Output>) => void;
}

interface ToolDefinition<Input, Output> {
  name: string;
  description: string;
  parameters: Record<string, any>;
  handler: (input: Input) => Promise<Output>;
}

export function registerAdminSyncTool(api: ToolRegistry, httpClient: HttpClient, config: KnowledgeRadarConfig): void {
  api.registerTool<AdminSyncInput, AdminSyncOutput>({
    name: 'knowledge_radar.admin_sync',
    description: '执行管理员级别的数据同步操作，同步飞书各数据源（消息、文档、日历、任务等）到知识雷达系统',
    parameters: {
      type: 'object',
      required: ['syncType'],
      properties: {
        syncType: {
          type: 'string',
          enum: ['full', 'incremental'],
          description: '同步类型：全量同步(full)、增量同步(incremental)',
        },
        sources: {
          type: 'array',
          items: {
            type: 'string',
            enum: ['im', 'doc', 'calendar', 'task', 'base', 'wiki', 'mail'],
          },
          description: '要同步的数据源列表，默认同步所有数据源',
        },
        startTime: {
          type: 'string',
          description: '增量同步的开始时间，ISO 8601格式，仅增量同步时生效',
        },
        workspaceId: {
          type: 'string',
          description: '工作空间ID，默认使用配置的defaultWorkspaceId',
        },
        async: {
          type: 'boolean',
          description: '是否异步执行，异步执行时立即返回任务ID',
          default: true,
        },
      },
    },
    async handler(input: AdminSyncInput): Promise<AdminSyncOutput> {
      const requestBody: AdminSyncInput = {
        ...input,
        workspaceId: input.workspaceId || config.defaultWorkspaceId,
      };

      return httpClient.post<AdminSyncOutput>('/v1/admin/sync', requestBody);
    },
  });
}
