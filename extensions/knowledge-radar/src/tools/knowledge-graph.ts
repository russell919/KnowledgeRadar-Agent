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

export interface KnowledgeGraphInput {
  mode?: 'graph' | 'graphrag';
  action?: 'traverse' | 'context' | 'impact' | 'project-overview';
  entityId?: string;
  entityName?: string;
  entityNames?: string[];
  projectName?: string;
  documentName?: string;
  maxDepth?: number;
  limit?: number;
  threshold?: number;
}

export interface EntityNode {
  entity_id: string;
  name: string;
  entity_type: string;
  mention_count: number;
}

export interface RelationEdge {
  source_entity_id: string;
  source_name: string;
  source_type: string;
  target_entity_id: string;
  target_name: string;
  target_type: string;
  relation_type: string;
  weight: number;
}

export interface KnowledgeGraphOutput {
  success: boolean;
  nodes?: EntityNode[];
  edges?: RelationEdge[];
  total?: number;
  context?: any;
  impact?: any;
  overview?: any;
  error?: string;
}

export function registerKnowledgeGraphTool(api: ToolRegistry, httpClient: HttpClient): void {
  api.registerTool<KnowledgeGraphInput, KnowledgeGraphOutput>({
    name: 'knowledge_radar.get_knowledge_graph',
    description: `获取知识图谱和 GraphRAG 分析。支持两种模式：
1. graph（默认）：实体关系网络查询，分析项目-人员-决策关联
2. graphrag：GraphRAG 增强分析，支持4种 action：
   - traverse: 关系加权遍历，沿实体关系边发现关联网络
   - context: 为实体集合聚合关联知识（决策/任务/风险/人员/项目）
   - impact: 文档变更影响分析（影响的项目/人员/待办）
   - project-overview: 项目全景图（新人入职脉络生成）`,
    parameters: {
      type: 'object',
      properties: {
        mode: {
          type: 'string',
          enum: ['graph', 'graphrag'],
          description: '分析模式：graph=实体关系图，graphrag=增强分析',
          default: 'graph',
        },
        action: {
          type: 'string',
          enum: ['traverse', 'context', 'impact', 'project-overview'],
          description: 'GraphRAG 动作（mode=graphrag时使用）',
        },
        entityId: {
          type: 'string',
          description: '实体ID（可选），graph模式使用',
        },
        entityName: {
          type: 'string',
          description: '实体名称（可选），graph或graphrag.traverse使用',
        },
        entityNames: {
          type: 'array',
          items: { type: 'string' },
          description: '实体名称列表，graphrag.context使用',
        },
        projectName: {
          type: 'string',
          description: '项目名称，graphrag.project-overview使用',
        },
        documentName: {
          type: 'string',
          description: '文档名称，graphrag.impact使用',
        },
        maxDepth: {
          type: 'number',
          description: '关系遍历深度，默认1',
          default: 1,
        },
        limit: {
          type: 'number',
          description: '返回节点数量上限，默认200',
          default: 200,
        },
      },
    },
    async handler(input: KnowledgeGraphInput): Promise<KnowledgeGraphOutput> {
      if (input.mode === 'graphrag') {
        // Route to GraphRAG engine
        return httpClient.post<KnowledgeGraphOutput>('/v1/knowledge/graphrag', {
          action: input.action || 'context',
          entityName: input.entityName,
          entityNames: input.entityNames,
          projectName: input.projectName,
          documentName: input.documentName,
          maxDepth: input.maxDepth,
          maxNodes: input.limit,
        });
      }
      // Default: entity graph
      return httpClient.post<KnowledgeGraphOutput>('/v1/knowledge/graph', {
        entityId: input.entityId,
        entityName: input.entityName,
        maxDepth: input.maxDepth,
        limit: input.limit,
      });
    },
  });
}
