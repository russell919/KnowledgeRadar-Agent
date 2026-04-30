import type { HttpClient } from '../http-client';
import type { KnowledgeRadarConfig } from '../config';
import type { IngestEventInput, IngestEventOutput } from '../types';

interface ToolRegistry {
  registerTool: <Input, Output>(tool: ToolDefinition<Input, Output>) => void;
}

interface ToolDefinition<Input, Output> {
  name: string;
  description: string;
  parameters: Record<string, any>;
  handler: (input: Input) => Promise<Output>;
}

export function registerIngestEventTool(api: ToolRegistry, httpClient: HttpClient, config: KnowledgeRadarConfig): void {
  api.registerTool<IngestEventInput, IngestEventOutput>({
    name: 'knowledge_radar.ingest_event',
    description: '摄入外部事件到知识雷达系统，包括消息、文档更新、会议结束、任务变更、用户入组等事件',
    parameters: {
      type: 'object',
      required: ['eventType', 'sourceId', 'sourceType', 'data'],
      properties: {
        eventType: {
          type: 'string',
          enum: ['message', 'document_updated', 'document_created', 'meeting_ended', 'task_updated', 'user_joined', 'custom'],
          description: '事件类型：消息(message)、文档更新(document_updated)、文档创建(document_created)、会议结束(meeting_ended)、任务更新(task_updated)、用户入组(user_joined)、自定义(custom)',
        },
        sourceId: {
          type: 'string',
          description: '事件源ID，如消息ID、文档ID、会议ID等',
        },
        sourceType: {
          type: 'string',
          enum: ['im', 'doc', 'calendar', 'task', 'base', 'wiki', 'mail'],
          description: '事件源类型：即时通讯(im)、文档(doc)、日历(calendar)、任务(task)、多维表格(base)、知识库(wiki)、邮箱(mail)',
        },
        data: {
          type: 'object',
          description: '事件数据，包含事件的具体内容',
        },
        eventTime: {
          type: 'string',
          description: '事件发生时间，ISO 8601格式，如：2026-04-24T10:00:00+08:00',
        },
        workspaceId: {
          type: 'string',
          description: '工作空间ID，默认使用配置的defaultWorkspaceId',
        },
      },
    },
    async handler(input: IngestEventInput): Promise<IngestEventOutput> {
      const requestBody: IngestEventInput = {
        ...input,
        workspaceId: input.workspaceId || config.defaultWorkspaceId,
        eventTime: input.eventTime || new Date().toISOString(),
      };

      return httpClient.post<IngestEventOutput>('/v1/ingest-event', requestBody);
    },
  });
}
