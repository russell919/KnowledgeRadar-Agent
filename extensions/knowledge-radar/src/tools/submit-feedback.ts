import type { HttpClient } from '../http-client';
import type { KnowledgeRadarConfig } from '../config';
import type { SubmitFeedbackInput, SubmitFeedbackOutput } from '../types';

interface ToolRegistry {
  registerTool: <Input, Output>(tool: ToolDefinition<Input, Output>) => void;
}

interface ToolDefinition<Input, Output> {
  name: string;
  description: string;
  parameters: Record<string, any>;
  handler: (input: Input) => Promise<Output>;
}

export function registerSubmitFeedbackTool(api: ToolRegistry, httpClient: HttpClient, config: KnowledgeRadarConfig): void {
  api.registerTool<SubmitFeedbackInput, SubmitFeedbackOutput>({
    name: 'knowledge_radar.submit_feedback',
    description: '提交用户对知识雷达推送内容的反馈，用于改进推送质量和更新用户画像',
    parameters: {
      type: 'object',
      required: ['executionId', 'feedbackType', 'content'],
      properties: {
        executionId: {
          type: 'string',
          description: '关联的执行ID，即run_scene返回的executionId',
        },
        feedbackType: {
          type: 'string',
          enum: ['useful', 'not_useful', 'incorrect', 'other'],
          description: '反馈类型：有帮助(useful)、无帮助(not_useful)、内容错误(incorrect)、其他(other)',
        },
        content: {
          type: 'string',
          description: '反馈内容，描述用户对推送内容的具体感受或建议',
        },
        userId: {
          type: 'string',
          description: '用户ID（可选），默认使用当前用户ID',
        },
        metadata: {
          type: 'object',
          description: '额外元数据（可选），如阅读时长、点击次数等',
        },
      },
    },
    async handler(input: SubmitFeedbackInput): Promise<SubmitFeedbackOutput> {
      return httpClient.post<SubmitFeedbackOutput>('/v1/feedback', input);
    },
  });
}
