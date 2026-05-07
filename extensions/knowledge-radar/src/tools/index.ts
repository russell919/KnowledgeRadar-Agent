import type { HttpClient } from '../http-client';
import type { KnowledgeRadarConfig } from '../config';
import { registerRunSceneTool } from './run-scene';
import { registerIngestEventTool } from './ingest-event';
import { registerSubmitFeedbackTool } from './submit-feedback';
import { registerPreviewActionTool } from './preview-action';
import { registerAdminSyncTool } from './admin-sync';
import { registerTrackBehaviorTool } from './track-behavior';
import { registerSearchKnowledgeTool } from './search-knowledge';
import { registerKnowledgeGraphTool } from './knowledge-graph';

interface ToolRegistry {
  registerTool: <Input, Output>(tool: {
    name: string;
    description: string;
    parameters: Record<string, any>;
    handler: (input: Input) => Promise<Output>;
  }) => void;
}

export function registerAllTools(api: ToolRegistry, httpClient: HttpClient, config: KnowledgeRadarConfig): void {
  // Phase 1 tools (original 5)
  registerRunSceneTool(api, httpClient, config);
  registerIngestEventTool(api, httpClient, config);
  registerSubmitFeedbackTool(api, httpClient, config);
  registerPreviewActionTool(api, httpClient, config);
  registerAdminSyncTool(api, httpClient, config);
  
  // Phase 2 tools (new - expose full backend capabilities)
  registerTrackBehaviorTool(api, httpClient);
  registerSearchKnowledgeTool(api, httpClient);
  registerKnowledgeGraphTool(api, httpClient);
}
