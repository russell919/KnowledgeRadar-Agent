import type { HttpClient } from './http-client';
import type { KnowledgeRadarConfig } from './config';

/**
 * 注册知识雷达相关命令
 * 
 * 根据OpenClaw官方SDK，命令注册使用 api.registerCommand
 * 
 * 命令列表：
 * - /knowledge-radar weekly: 触发每周知识推送
 * - /knowledge-radar meeting: 触发会前简报
 * - /knowledge-radar doc-change: 触发文档变更提醒
 * - /knowledge-radar onboarding: 触发新人入职引导
 * - /knowledge-radar sync: 触发数据同步
 * 
 * @param api OpenClaw API实例
 * @param httpClient HTTP客户端
 * @param config 插件配置
 */
export function registerCommands(api: { registerCommand: (command: CommandDefinition) => void }, httpClient: HttpClient, config: KnowledgeRadarConfig): void {
  /**
   * 注册 /knowledge-radar weekly 命令
   * 触发每周知识推送场景
   */
  api.registerCommand({
    name: 'knowledge-radar weekly',
    description: '触发知识雷达每周知识推送',
    handler: async () => {
      return httpClient.post('/v1/run-scene', {
        sceneType: 'weekly_digest',
        workspaceId: config.defaultWorkspaceId,
      });
    },
  });

  /**
   * 注册 /knowledge-radar meeting 命令
   * 触发会前简报场景
   */
  api.registerCommand({
    name: 'knowledge-radar meeting',
    description: '触发知识雷达会前简报',
    handler: async () => {
      return httpClient.post('/v1/run-scene', {
        sceneType: 'meeting_briefing',
        workspaceId: config.defaultWorkspaceId,
      });
    },
  });

  /**
   * 注册 /knowledge-radar doc-change 命令
   * 触发文档变更场景
   */
  api.registerCommand({
    name: 'knowledge-radar doc-change',
    description: '触发知识雷达文档变更提醒',
    handler: async () => {
      return httpClient.post('/v1/run-scene', {
        sceneType: 'doc_change',
        workspaceId: config.defaultWorkspaceId,
      });
    },
  });

  /**
   * 注册 /knowledge-radar onboarding 命令
   * 触发新人入职引导场景
   */
  api.registerCommand({
    name: 'knowledge-radar onboarding',
    description: '触发知识雷达新人入职引导',
    handler: async () => {
      return httpClient.post('/v1/run-scene', {
        sceneType: 'onboarding',
        workspaceId: config.defaultWorkspaceId,
      });
    },
  });

  /**
   * 注册 /knowledge-radar sync 命令
   * 触发数据同步
   */
  api.registerCommand({
    name: 'knowledge-radar sync',
    description: '触发知识雷达数据同步',
    handler: async () => {
      return httpClient.post('/v1/admin/sync', {
        syncType: 'incremental',
        workspaceId: config.defaultWorkspaceId,
        async: true,
      });
    },
  });
}

/**
 * 命令定义接口
 */
interface CommandDefinition {
  name: string;
  description: string;
  handler: () => Promise<any>;
}
