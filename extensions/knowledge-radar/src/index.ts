/**
 * 知识雷达 OpenClaw 插件入口
 * 
 * 本插件负责：
 * 1. 注册知识雷达相关工具
 * 2. 加载插件内置skill
 * 3. 将请求转发给Python后端处理
 */

import { definePluginEntry } from 'openclaw/plugin-sdk/plugin-entry';
import { validateConfig, type KnowledgeRadarConfig } from './config';
import { HttpClient } from './http-client';
import { registerAllTools } from './tools';
import { registerCommands } from './commands';

/**
 * 插件入口定义
 */
export default definePluginEntry({
  id: 'knowledge-radar',
  name: '知识雷达',
  version: '1.0.0',
  description: '企业知识整合与分发Agent，支持知识推送、会前简报、文档变更提醒、新人入职引导等场景',
  
  /**
   * 插件初始化函数
   * OpenClaw会调用此函数来加载插件
   */
  async setup(api, config) {
    // 验证配置
    let validatedConfig: KnowledgeRadarConfig;
    try {
      validatedConfig = validateConfig(config);
    } catch (error) {
      console.error('[knowledge-radar] 配置验证失败:', error);
      throw error;
    }

    // 创建HTTP客户端
    const httpClient = new HttpClient(validatedConfig);

    // 注册所有工具
    console.log('[knowledge-radar] 开始注册工具...');
    registerAllTools(api, httpClient, validatedConfig);
    console.log('[knowledge-radar] 工具注册完成');

    // 注册命令
    console.log('[knowledge-radar] 开始注册命令...');
    registerCommands(api, httpClient, validatedConfig);
    console.log('[knowledge-radar] 命令注册完成');

    console.log('[knowledge-radar] 插件初始化完成');
  },

  /**
   * 插件卸载函数（可选）
   * OpenClaw在卸载插件时会调用此函数
   */
  async cleanup() {
    console.log('[knowledge-radar] 插件已卸载');
  },
});

// 导出类型供外部使用
export type { KnowledgeRadarConfig } from './config';
export type * from './types';
