import type { HttpClient } from '../http-client';
import type { KnowledgeRadarConfig } from '../config';
import { registerRunSceneTool } from './run-scene';
import { registerIngestEventTool } from './ingest-event';
import { registerSubmitFeedbackTool } from './submit-feedback';
import { registerPreviewActionTool } from './preview-action';
import { registerAdminSyncTool } from './admin-sync';

interface ToolRegistry {
  registerTool: <Input, Output>(tool: {
    name: string;
    description: string;
    parameters: Record<string, any>;
    handler: (input: Input) => Promise<Output>;
  }) => void;
}

export function registerAllTools(api: ToolRegistry, httpClient: HttpClient, config: KnowledgeRadarConfig): void {
  registerRunSceneTool(api, httpClient, config);
  registerIngestEventTool(api, httpClient, config);
  registerSubmitFeedbackTool(api, httpClient, config);
  registerPreviewActionTool(api, httpClient, config);
  registerAdminSyncTool(api, httpClient, config);
}
