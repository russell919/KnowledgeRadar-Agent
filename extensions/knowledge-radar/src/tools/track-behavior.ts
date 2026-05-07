import type { HttpClient } from '../http-client';
import type { KnowledgeRadarConfig } from '../config';

interface ToolRegistry {
  registerTool: <Input, Output>(tool: ToolDefinition<Input, Output>) => void;
}

interface ToolDefinition<Input, Output> {
  name: string;
  description: string;
  parameters: Record<string, any>;
  handler: (input: Input) => Promise<Output>;
}

export interface TrackBehaviorInput {
  userId: string;
  type: 'click' | 'read' | 'follow_up' | 'collect' | 'negative_feedback' | 'dismiss' | 'reply' | 'search';
  knowledgeId?: string;
  knowledgeType?: string;
  content?: string;
  timestamp?: number;
}

export interface TrackBehaviorOutput {
  success: boolean;
  message: string;
  profileUpdated: boolean;
}

export function registerTrackBehaviorTool(api: ToolRegistry, httpClient: HttpClient): void {
  api.registerTool<TrackBehaviorInput, TrackBehaviorOutput>({
    name: 'knowledge_radar.track_behavior',
    description: '记录用户行为事件，用于更新用户画像和优化推送质量。包括点击、阅读、追问、收藏、负反馈、忽略、回复、搜索等行为类型',
    parameters: {
      type: 'object',
      required: ['userId', 'type'],
      properties: {
        userId: {
          type: 'string',
          description: '用户ID',
        },
        type: {
          type: 'string',
          enum: ['click', 'read', 'follow_up', 'collect', 'negative_feedback', 'dismiss', 'reply', 'search'],
          description: '行为类型：点击(click)、阅读(read)、追问(follow_up)、收藏(collect)、负反馈(negative_feedback)、忽略(dismiss)、回复(reply)、搜索(search)',
        },
        knowledgeId: {
          type: 'string',
          description: '关联的知识ID（可选）',
        },
        knowledgeType: {
          type: 'string',
          description: '知识类型（可选）',
        },
        content: {
          type: 'string',
          description: '用户的具体行为内容（可选），如追问的问题或搜索的查询',
        },
        timestamp: {
          type: 'number',
          description: '行为发生时间戳（可选），默认当前时间',
        },
      },
    },
    async handler(input: TrackBehaviorInput): Promise<TrackBehaviorOutput> {
      return httpClient.post<TrackBehaviorOutput>('/v1/track-behavior', {
        ...input,
        timestamp: input.timestamp || Date.now(),
      });
    },
  });
}
