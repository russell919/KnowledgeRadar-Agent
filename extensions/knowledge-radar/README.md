# Knowledge Radar OpenClaw Plugin

飞书/Lark 版知识雷达 OpenClaw 插件

## 概述

Knowledge Radar 是一个企业知识整合与分发 Agent，基于 OpenClaw + 飞书/Lark 实现。

### 核心能力

1. **知识整合**: 将分散在文档、群聊、会议纪要、任务、多维表格中的信息统一入库
2. **场景理解**: 根据触发事件判断当前办公场景
3. **精准分发**: 结合权限、用户画像、知识重要性、反打扰策略决定推送对象和内容
4. **持续沉淀**: 根据反馈更新用户画像，把高频知识沉淀为 FAQ/SOP/项目记忆

### 四大核心场景

| 场景 | 触发命令 | 说明 |
|------|----------|------|
| `weekly_digest` | `/knowledge-radar weekly` | 每周知识推送 |
| `meeting_briefing` | `/knowledge-radar meeting` | 会前简报 |
| `doc_change` | `/knowledge-radar doc-change` | 文档变更提醒 |
| `onboarding` | `/knowledge-radar onboarding` | 新人入职引导 |

## 文件结构

```
knowledge-radar/
├── openclaw.plugin.json     # 插件清单
├── package.json              # NPM 配置
├── tsconfig.json             # TypeScript 配置
├── src/
│   ├── index.ts              # 插件入口
│   ├── config.ts             # 配置 Schema
│   ├── http-client.ts        # HTTP 客户端
│   ├── types.ts              # 类型定义
│   ├── commands.ts           # 命令注册
│   └── tools/                # 工具实现
│       ├── index.ts
│       ├── run-scene.ts
│       ├── ingest-event.ts
│       ├── submit-feedback.ts
│       ├── preview-action.ts
│       └── admin-sync.ts
├── skills/
│   └── knowledge-radar/
│       └── SKILL.md          # Skill 定义
└── dist/                     # 编译输出
```

## 安装

### 方式一：集成到 OpenClaw

1. 复制到 OpenClaw 扩展目录：

```bash
cp -r extensions/knowledge-radar <OPENCLAW_ROOT>/extensions/
```

2. 编译插件：

```bash
cd <OPENCLAW_ROOT>/extensions/knowledge-radar
npm install
npm run build
```

3. 配置插件：

在 OpenClaw 配置中添加：

```json
{
  "plugins": {
    "entries": {
      "knowledge-radar": {
        "enabled": true
      }
    }
  }
}
```

### 方式二：独立开发

```bash
npm install
npm run dev    # 开发模式 (watch)
npm run build  # 生产构建
```

## 配置

插件配置通过 OpenClaw 配置文件传入：

```json
{
  "plugins": {
    "entries": {
      "knowledge-radar": {
        "enabled": true,
        "config": {
          "backendBaseUrl": "http://localhost:8787",
          "apiKey": "dev-local-key",
          "defaultWorkspaceId": "apollo-workspace",
          "enableHumanPreview": true
        }
      }
    }
  }
}
```

### 配置参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `backendBaseUrl` | string | 是 | 后端服务地址 |
| `apiKey` | string | 否 | API 密钥 |
| `defaultWorkspaceId` | string | 否 | 默认工作空间 ID |
| `enableHumanPreview` | boolean | 否 | 是否启用人工预览 |

## 工具

插件提供以下 OpenClaw 工具：

### 1. knowledge_radar.run_scene

运行知识雷达场景

```typescript
await api.callTool('knowledge_radar.run_scene', {
  sceneType: 'weekly_digest',
  workspaceId: 'apollo-workspace',
  dryRun: false
});
```

### 2. knowledge_radar.ingest_event

摄入外部事件

```typescript
await api.callTool('knowledge_radar.ingest_event', {
  eventType: 'document_updated',
  sourceId: 'doc_123',
  sourceType: 'doc',
  data: { title: 'xxx' },
  eventTime: '2024-05-01T10:00:00Z'
});
```

### 3. knowledge_radar.submit_feedback

提交用户反馈

```typescript
await api.callTool('knowledge_radar.submit_feedback', {
  executionId: 'exec_xxx',
  feedbackType: 'useful',
  content: '很有帮助'
});
```

### 4. knowledge_radar.preview_action

预览动作（用于人工确认）

```typescript
await api.callTool('knowledge_radar.preview_action', {
  actionType: 'push_content',
  params: { targetUsers: ['user1', 'user2'] }
});
```

### 5. knowledge_radar.admin_sync

管理员数据同步

```typescript
await api.callTool('knowledge_radar.admin_sync', {
  syncType: 'incremental',
  sources: ['doc', 'chat'],
  async: true
});
```

## 命令

插件注册以下 Slash 命令：

| 命令 | 说明 |
|------|------|
| `/knowledge-radar weekly` | 触发每周知识推送 |
| `/knowledge-radar meeting` | 触发会前简报 |
| `/knowledge-radar doc-change` | 触发文档变更提醒 |
| `/knowledge-radar onboarding` | 触发新人入职引导 |
| `/knowledge-radar sync` | 触发数据同步 |

## Skill

Skill 文件位于 `skills/knowledge-radar/SKILL.md`

### 前置条件

使用本插件的 Skill 前，需要先读取 `lark-shared/SKILL.md` 了解认证和权限处理。

### 使用示例

```
用户：帮我生成会前简报
-> 调用 knowledge_radar.run_scene(sceneType="meeting_briefing")

用户：这周有什么重要知识需要关注
-> 调用 knowledge_radar.run_scene(sceneType="weekly_digest")
```

## 开发

### 类型检查

```bash
npm run typecheck
```

### 构建

```bash
npm run build
```

### 清理

```bash
npm run clean
```

## 待确认项

以下项目需要参考官方文档确认：

- [ ] OpenClaw SDK 的实际 import path
- [ ] `openclaw/plugin-sdk/plugin-entry` 模块的完整 API
- [ ] `agents.defaults.skills` 的正确格式
- [ ] 插件配置文件的 schema

详见 [INTEGRATION_GAPS.md](../../apps/knowledge-radar-agent/docs/INTEGRATION_GAPS.md)

## 许可

MIT
