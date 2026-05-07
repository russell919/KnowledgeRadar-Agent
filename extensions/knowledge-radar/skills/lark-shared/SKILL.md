---
name: lark-shared
version: 2.0.0
description: "飞书/Lark 共享技能 — 认证、权限和通用操作。知识雷达 v2.0 的前置依赖。"
---

# Lark 共享技能

## 用途

本技能提供飞书/Lark 生态中多个技能（如 knowledge-radar v2.0、lark-im、lark-doc）共享的认证、权限和通用工具能力。

## 认证方式

知识雷达 Agent 通过以下方式访问飞书数据：

### 方式一：飞书 Open API（当前使用）

通过飞书开放平台的自建应用或用户 token：
- `FEISHU_TOKEN` — 用户访问令牌（user_access_token）
- 存储在 `.env` 文件或环境变量中

当前后端 `server.js` 使用 `FeishuClient` 直接通过 HTTP 调用飞书 Open API：
```
BASE = 'https://open.feishu.cn/open-apis'
headers = { Authorization: Bearer <FEISHU_TOKEN> }
```

### 方式二：@larksuite/cli（可选）

```bash
# 安装 CLI
npm install -g @larksuite/cli

# 登录（浏览器 OAuth）
lark-cli login

# 验证登录状态
lark-cli whoami
```

## 权限检查

在调用任何飞书数据前，确认以下权限 scopes 已开启：

| 资源 | 权限 | scope |
|------|------|-------|
| 文档 | 查看 | docx:document:readonly |
| 消息 | 查看 | im:message |
| 日历 | 查看 | calendar:calendar:readonly |
| 任务 | 查看 | task:task:readonly |
| 多维表格 | 查看 | bitable:app:readonly |
| 通讯录 | 查看 | contact:user.base:readonly |

## 知识雷达 v2.0 权限策略

知识雷达的每个场景在推送前会进行权限过滤：

1. **知识源权限**：从飞书 API 获取的内容继承原始权限（聊天、文档、日历）
2. **推送对象过滤**：`PushScore` 的权限维度考虑用户可见范围，取最严原则
3. **手动检索注意**：直接调用 `search_knowledge` 时，Agent 应确认检索内容不超越用户权限

## 通用工具

本技能提供以下通用工具供其他技能调用：

- `lark_shared.get_current_user` — 获取当前飞书用户信息
- `lark_shared.check_permission` — 检查当前用户是否有权访问指定资源
- `lark_shared.resolve_user_id` — 解析用户标识（open_id ↔ user_id ↔ 姓名）

## 参考

- [knowledge-radar SKILL.md](../knowledge-radar/SKILL.md) — 知识雷达 v2.0 Agent 工作流
