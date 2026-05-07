import { z } from 'zod';

/**
 * 知识雷达插件配置Schema
 */
export const KnowledgeRadarConfigSchema = z.object({
  /** 后端服务基础URL */
  backendBaseUrl: z.string().url('backendBaseUrl必须是有效的URL地址'),
  /** API访问密钥 */
  apiKey: z.string().optional(),
  /** 默认工作空间ID */
  defaultWorkspaceId: z.string().optional(),
  /** 是否启用人工预览确认 */
  enableHumanPreview: z.boolean().default(true),
});

/**
 * 知识雷达插件配置类型
 */
export type KnowledgeRadarConfig = z.infer<typeof KnowledgeRadarConfigSchema>;

/**
 * 验证并解析配置
 * @param config 原始配置对象
 * @returns 验证后的配置对象
 * @throws 如果配置验证失败，抛出ZodError
 */
export function validateConfig(config: unknown): KnowledgeRadarConfig {
  return KnowledgeRadarConfigSchema.parse(config);
}
