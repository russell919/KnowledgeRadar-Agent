/**
 * OpenClaw Plugin SDK 类型声明
 * 这些类型在运行时由 OpenClaw 提供
 */

declare module 'openclaw/plugin-sdk/plugin-entry' {
  export interface PluginOptions {
    id: string;
    name: string;
    version: string;
    description?: string;
    setup?: (api: PluginAPI, config: unknown) => Promise<void>;
    cleanup?: () => Promise<void>;
  }

  export interface PluginAPI {
    registerTool: <Input = any, Output = any>(tool: ToolDefinition<Input, Output>) => void;
    registerCommand: (command: CommandDefinition) => void;
    registerHook: (events: string | string[], handler: HookHandler) => void;
    registerGatewayMethod: (method: string, handler: GatewayMethodHandler) => void;
    registerHttpRoute: (params: HttpRouteParams) => void;
    registerService: (service: ServiceDefinition) => void;
  }

  export interface ToolDefinition<Input, Output> {
    name: string;
    description: string;
    parameters: Record<string, any>;
    handler: (input: Input) => Promise<Output>;
  }

  export interface CommandDefinition {
    name: string;
    description: string;
    handler: () => Promise<any>;
  }

  export type HookHandler = (event: HookEvent) => Promise<void> | void;

  export interface HookEvent {
    type: string;
    payload: any;
  }

  export type GatewayMethodHandler = (params: Record<string, any>) => Promise<any>;

  export interface HttpRouteParams {
    method: 'GET' | 'POST' | 'PUT' | 'DELETE';
    path: string;
    handler: (req: any, res: any) => Promise<void> | void;
  }

  export interface ServiceDefinition {
    name: string;
    start: () => Promise<void>;
    stop: () => Promise<void>;
  }

  export function definePluginEntry(options: PluginOptions): PluginEntry;

  export interface PluginEntry {
    id: string;
    name: string;
    version: string;
    description?: string;
  }
}
