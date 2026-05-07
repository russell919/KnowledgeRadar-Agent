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

export interface SearchKnowledgeInput {
  query: string;
  mode?: 'hybrid' | 'semantic' | 'keyword';
  topK?: number;
  filter?: {
    type?: string;
    sourceType?: string;
    sinceDays?: number;
    entities?: string[];
  };
}

export interface SearchKnowledgeOutput {
  results: Array<{
    id: string;
    text: string;
    score: number;
    metadata: Record<string, any>;
    scores: {
      semantic: number;
      keyword: number;
      recency: number;
      reranker: number;
    };
  }>;
  total: number;
  searchMode: string;
}

export function registerSearchKnowledgeTool(api: ToolRegistry, httpClient: HttpClient): void {
  api.registerTool<SearchKnowledgeInput, SearchKnowledgeOutput>({
    name: 'knowledge_radar.search_knowledge',
    description: '混合检索知识库。支持 Hybrid Search（语义+关键词+重排）、纯语义检索、纯关键词检索三种模式。可用于会前简报的信息搜索、新人必读材料检索、文档变更影响分析等场景',
    parameters: {
      type: 'object',
      required: ['query'],
      properties: {
        query: {
          type: 'string',
          description: '搜索查询语句。建议包含关键实体名称、项目名、人名等，以提高检索相关性',
        },
        mode: {
          type: 'string',
          enum: ['hybrid', 'semantic', 'keyword'],
          description: '检索模式：混合模式(hybrid)使用语义+关键词+重排三通道、纯语义(semantic)使用Embedding相似度、纯关键词(keyword)使用BM25。默认hybrid',
          default: 'hybrid',
        },
        topK: {
          type: 'number',
          description: '返回结果数量上限，默认20',
          default: 20,
        },
        filter: {
          type: 'object',
          description: '检索过滤条件（可选）',
          properties: {
            type: {
              type: 'string',
              description: '按知识类型过滤：decision/action_item/risk/update/info',
            },
            sourceType: {
              type: 'string',
              description: '按来源类型过滤：im/doc/calendar/task',
            },
            sinceDays: {
              type: 'number',
              description: '仅搜索最近N天内的内容',
            },
            entities: {
              type: 'array',
              items: { type: 'string' },
              description: '仅搜索包含指定实体的内容',
            },
          },
        },
      },
    },
    async handler(input: SearchKnowledgeInput): Promise<SearchKnowledgeOutput> {
      return httpClient.post<SearchKnowledgeOutput>('/v1/knowledge/search', input);
    },
  });
}
