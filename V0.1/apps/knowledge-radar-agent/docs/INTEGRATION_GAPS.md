# 集成缺口文档

本文档列出了 Knowledge Radar 项目中所有需要进一步人工确认的集成接口。这些接口在代码中标记为 `TODO_FEISHU_DOC_LOOKUP` 或 `TODO_OPENCLAW_SDK_LOOKUP`。

---

## 1. 飞书 CLI 客户端 (FeishuCLIClient)

**文件**: `apps/knowledge-radar-agent/src/knowledge_radar/integrations/feishu_client.py`

**问题**: 尚未确认飞书 CLI 的官方命令格式和参数

### 1.1 需要确认的 CLI 命令

| 方法 | 待确认内容 | 参考文档 |
|------|-----------|---------|
| `read_doc` | 读取文档内容的 CLI 命令格式 | [飞书文档 API](https://open.feishu.cn/document/home/index) |
| `read_chat_history` | 读取聊天历史的命令和参数 | 同上 |
| `read_meeting_note` | 读取会议纪要的命令 | 同上 |
| `read_calendar_event` | 读取日历事件的命令 | 同上 |
| `read_task` | 读取任务的命令 | 同上 |
| `read_bitable` | 读取多维表格的命令 | 同上 |
| `send_card` | 发送卡片的命令格式 | 同上 |

### 1.2 待确认的 CLI 配置

| 项目 | 待确认内容 |
|------|-----------|
| 官方包名 | `@larksuite/cli` 或 `lark-cli` 或其他？ |
| 安装命令 | `npm install -g @larksuite/cli` 或其他？ |
| login/logout 命令 | 参数和认证流程 |
| token-mode 参数 | 如何指定 token 模式 |
| MCP 模式 | `--mcp` flag 的确切行为 |
| 工具集裁剪 | 如何指定可用的工具子集 |

**临时方案**: 当前使用 `MockFeishuClient` 进行 Demo 和测试

---

## 2. 飞书卡片格式

**文件**:
- `apps/knowledge-radar-agent/src/knowledge_radar/services/card_service.py`
- `apps/knowledge-radar-agent/src/knowledge_radar/schemas/cards.py`

### 2.1 待确认的卡片元素

| 元素 | 待确认内容 |
|------|-----------|
| 卡片模板 | 飞书官方支持的卡片模板类型 |
| 交互元素 | button, select 等交互元素的配置 |
| 消息推送 | `send_card` 的 payload 格式 |

**临时方案**: 使用简化卡片格式，发送前带警告提示

---

## 3. API 路由待确认项

**文件**: `apps/knowledge-radar-agent/src/knowledge_radar/api/`

### 3.1 routes_admin.py

| 行号 | 待确认内容 |
|------|-----------|
| 123 | 管理员权限的验证方式 |
| 172 | 索引重建的队列机制 |
| 204 | 全量同步的超时设置 |
| 233 | 知识过期策略的具体参数 |

### 3.2 routes_feedback.py

| 行号 | 待确认内容 |
|------|-----------|
| 60 | 反馈提交频率限制的具体值 |

### 3.3 routes_ingest.py

| 行号 | 待确认内容 |
|------|-----------|
| 96 | 事件去重的具体算法 |
| 141 | 批量处理的最佳并发数 |

---

## 4. 依赖注入待确认项

**文件**: `apps/knowledge-radar-agent/src/knowledge_radar/dependencies.py`

| 行号 | 待确认内容 |
|------|-----------|
| 89 | OpenClaw 客户端的初始化参数 |
| 124 | LLM 客户端的供应商选择 |
| 139 | 使用 `lark-oapi` 还是 `lark-cli` SDK |

---

## 5. OpenClaw SDK 待确认项

**文件**: `extensions/knowledge-radar/src/openclaw-sdk.d.ts`

### 5.1 SDK 类型定义

当前使用自行声明的类型定义 (`declare module`)，需要确认：

| 项目 | 待确认内容 |
|------|-----------|
| `definePluginEntry` | 实际的 import path 是否为 `openclaw/plugin-sdk/plugin-entry` |
| `registerTool` | 是否支持泛型参数 |
| `registerCommand` | 命令参数的具体结构 |
| `registerHook` | 支持的事件类型 |
| `registerGatewayMethod` | 方法注册的具体用法 |

### 5.2 运行时类型验证

**问题**: 代码中使用了 TypeScript 类型声明，但运行时类型由 OpenClaw 提供

**建议**: 在官方 SDK 包发布后，移除 `src/openclaw-sdk.d.ts` 并使用官方类型

---

## 6. Skills 配置待确认项

**文件**: `extensions/knowledge-radar/skills/knowledge-radar/SKILL.md`

### 6.1 frontmatter

| 字段 | 当前值 | 待确认 |
|------|--------|--------|
| `bins` | `["lark-cli"]` | 是否正确？是否有其他依赖？ |

### 6.2 技能触发

当前设计的技能触发方式：
```
用户：帮我生成会前简报
-> 调用 knowledge_radar.run_scene(sceneType="meeting_briefing")
```

需要确认：
- OpenClaw 中 skill 如何被 Agent 调用
- 是否需要显式注册到 `agents.defaults.skills`

---

## 7. 配置文件格式

**文件**:
- `configs/knowledge-radar.example.json`
- `extensions/knowledge-radar/openclaw.plugin.json`

### 7.1 openclaw.plugin.json

当前配置需要确认是否符合 OpenClaw 最新版本：

```json
{
  "id": "knowledge-radar",
  "name": "知识雷达",
  "skills": ["skills"]
}
```

需要确认：
- `skills` 字段是否为相对路径
- 是否需要 `entry` 字段指向编译后的 JS 文件

---

## 8. 环境变量

**文件**: `apps/knowledge-radar-agent/.env.example`

待确认的环境变量：

| 变量 | 用途 | 待确认默认值 |
|------|------|-------------|
| `LARK_APP_ID` | 飞书应用 ID | - |
| `LARK_APP_SECRET` | 飞书应用密钥 | - |
| `LARK_CLI_TOKEN` | CLI 认证 token | - |
| `OPENCLAW_PLUGIN_DIR` | 插件安装目录 | - |

---

## 9. 待人工确认清单

以下是需要开发者在接入前确认的项目：

### 9.1 高优先级 (阻塞开发)

- [ ] 飞书 CLI 包名和安装命令
- [ ] OpenClaw SDK 的实际 import path
- [ ] 飞书应用需要的权限 scopes

### 9.2 中优先级 (影响功能)

- [ ] 飞书卡片的官方格式
- [ ] OpenClaw 插件的配置文件格式
- [ ] 技能是否需要显式注册

### 9.3 低优先级 (可后续完善)

- [ ] API 限流的具体值
- [ ] 批量处理的最佳并发数
- [ ] 日志级别配置

---

## 10. 参考资源

- [飞书开放平台](https://open.feishu.cn/document/home/index)
- [飞书服务端 API](https://open.feishu.cn/document/server-docs)
- [飞书客户端 API](https://open.feishu.cn/document/client-docs)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw 官网](https://openclaw.ai/)

---

**最后更新**: 2024-05-01
