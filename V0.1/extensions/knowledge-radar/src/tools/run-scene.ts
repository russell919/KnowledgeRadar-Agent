import type { HttpClient } from '../http-client';
import type { KnowledgeRadarConfig } from '../config';
import type { RunSceneInput, RunSceneOutput } from '../types';

/**
 * 工具注册接口定义（来自OpenClaw SDK）
 */
interface ToolRegistry {
  registerTool: <Input, Output>(tool: ToolDefinition<Input, Output>) => void;
}

interface ToolDefinition<Input, Output> {
  name: string;
  description: string;
  parameters: Record<string, any>;
  handler: (input: Input) => Promise<Output>;
}

/**
 * 注册knowledge_radar.run_scene工具
 * 
 * 调用后端/v1/run-scene接口，执行指定的知识雷达场景
 */
export function registerRunSceneTool(api: ToolRegistry, httpClient: HttpClient, config: KnowledgeRadarConfig): void {
  api.registerTool<RunSceneInput, RunSceneOutput>({
    name: 'knowledge_radar.run_scene',
    description: '运行知识雷达指定场景，包括每周知识推送、会前简报、文档变更提醒、新人入职引导等',
    parameters: {
      type: 'object',
      required: ['sceneType'],
      properties: {
        sceneType: {
          type: 'string',
          enum: ['weekly_digest', 'meeting_briefing', 'doc_change', 'onboarding', 'manual'],
          description: '场景类型：每周知识推送(weekly_digest)、会前简报(meeting_briefing)、文档变更(doc_change)、新人入职(onboarding)、手动触发(manual)',
        },
        triggerId: {
          type: 'string',
          description: '触发源ID，如会议ID、文档ID等，用于关联特定触发事件',
        },
        workspaceId: {
          type: 'string',
          description: '工作空间ID，默认使用配置的defaultWorkspaceId',
        },
        params: {
          type: 'object',
          description: '自定义参数，用于传递场景特定的配置',
        },
        dryRun: {
          type: 'boolean',
          description: '是否为预览模式，仅返回预览内容不实际执行推送',
          default: false,
        },
      },
    },
    async handler(input: RunSceneInput): Promise<RunSceneOutput> {
      const requestBody: RunSceneInput = {
        ...input,
        workspaceId: input.workspaceId || config.defaultWorkspaceId,
      };

      return httpClient.post<RunSceneOutput>('/v1/run-scene', requestBody);
    },
  });
}
