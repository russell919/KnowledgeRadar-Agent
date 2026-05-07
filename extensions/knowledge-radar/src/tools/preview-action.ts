import type { HttpClient } from '../http-client';
import type { KnowledgeRadarConfig } from '../config';
import type { PreviewActionInput, PreviewActionOutput } from '../types';

interface ToolRegistry {
  registerTool: <Input, Output>(tool: ToolDefinition<Input, Output>) => void;
}

interface ToolDefinition<Input, Output> {
  name: string;
  description: string;
  parameters: Record<string, any>;
  handler: (input: Input) => Promise<Output>;
}

export function registerPreviewActionTool(api: ToolRegistry, httpClient: HttpClient, config: KnowledgeRadarConfig): void {
  api.registerTool<PreviewActionInput, PreviewActionOutput>({
    name: 'knowledge_radar.preview_action',
    description: '预览知识雷达即将执行的动作，包括推送内容、更新知识库、同步数据、发送通知等，用于人工确认',
    parameters: {
      type: 'object',
      required: ['actionType', 'params'],
      properties: {
        actionType: {
          type: 'string',
          enum: ['push_content', 'update_knowledge', 'sync_data', 'send_notification'],
          description: '动作类型：推送内容(push_content)、更新知识库(update_knowledge)、同步数据(sync_data)、发送通知(send_notification)',
        },
        params: {
          type: 'object',
          description: '动作参数，包含执行该动作所需的配置和数据',
        },
        workspaceId: {
          type: 'string',
          description: '工作空间ID，默认使用配置的defaultWorkspaceId',
        },
      },
    },
    async handler(input: PreviewActionInput): Promise<PreviewActionOutput> {
      const requestBody: PreviewActionInput = {
        ...input,
        workspaceId: input.workspaceId || config.defaultWorkspaceId,
      };

      return httpClient.post<PreviewActionOutput>('/v1/preview-action', requestBody);
    },
  });
}
