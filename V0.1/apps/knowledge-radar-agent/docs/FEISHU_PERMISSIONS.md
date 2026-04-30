# 飞书权限配置指南

本文档列出 Knowledge Radar 项目所需的飞书权限范围 (Scopes)，以及申请步骤。

---

## 1. 权限概述

Knowledge Radar 需要访问飞书的多个模块：
- 云文档 (Docs)
- 消息 (IM)
- 日历 (Calendar)
- 任务 (Tasks)
- 多维表格 (Bitable)
- 通讯录 (Contact)

---

## 2. 必需权限 Scopes

### 2.1 云文档 (Docs)

| Scope | 用途 | 权限级别 |
|-------|------|----------|
| `docx:document:readonly` | 读取文档内容 | 读 |
| `docx:document:write` | 创建/编辑文档 | 写 |
| `docx:file:readonly` | 读取文件 | 读 |
| `wiki:space:readonly` | 读取知识库空间 | 读 |
| `wiki:node:readonly` | 读取知识库节点 | 读 |

**待确认**:
- [ ] 是否有细粒度的"只读指定文档"权限？

### 2.2 消息 (IM)

| Scope | 用途 | 权限级别 |
|-------|------|----------|
| `im:message:readonly` | 读取消息 | 读 |
| `im:message:send_as_bot` | 以机器人发送消息 | 写 |
| `im:message:send` | 发送消息 | 写 |
| `im:chat:readonly` | 读取群组信息 | 读 |
| `im:chat:write` | 创建/编辑群组 | 写 |

**待确认**:
- [ ] `send_card` 是否需要额外的 scope？

### 2.3 日历 (Calendar)

| Scope | 用途 | 权限级别 |
|-------|------|----------|
| `calendar:event:readonly` | 读取日历事件 | 读 |
| `calendar:event:write` | 创建/编辑日历事件 | 写 |
| `calendar:calendar:readonly` | 读取日历 | 读 |

**待确认**:
- [ ] 是否需要 `calendar:acl` 权限？

### 2.4 任务 (Tasks)

| Scope | 用途 | 权限级别 |
|-------|------|----------|
| `task:task:readonly` | 读取任务 | 读 |
| `task:task:write` | 创建/编辑任务 | 写 |
| `task:subtask:readonly` | 读取子任务 | 读 |
| `task:subtask:write` | 创建子任务 | 写 |

**待确认**:
- [ ] 任务 API 的 scope 前缀是 `task` 还是 `tasks`？

### 2.5 多维表格 (Bitable)

| Scope | 用途 | 权限级别 |
|-------|------|----------|
| `bitable:app:readonly` | 读取多维表格 | 读 |
| `bitable:app:write` | 编辑多维表格 | 写 |

**待确认**:
- [ ] 是否需要表级别的权限控制？

### 2.6 通讯录 (Contact)

| Scope | 用途 | 权限级别 |
|-------|------|----------|
| `contact:user.base:readonly` | 读取用户基本信息 | 读 |
| `contact:user.email:readonly` | 读取用户邮箱 | 读 |
| `contact:department:readonly` | 读取部门信息 | 读 |

---

## 3. 权限申请步骤

### 3.1 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 进入「开发者后台」
3. 点击「创建应用」
4. 填写应用信息（名称、描述、图标）
5. 获取 `App ID` 和 `App Secret`

### 3.2 配置权限

1. 在应用详情页，点击「权限管理」
2. 点击「开通权限」
3. 搜索并添加上述必需权限
4. 提交审核（企业自建应用通常自动通过）

### 3.3 配置应用功能

1. **机器人**: 在「应用功能」中开启「机器人」
2. **消息订阅**: 开启「使用长连接接收消息」
3. **权限回调**: 配置权限审核回调 URL（可选）

---

## 4. 环境变量配置

在 `.env` 文件中配置：

```bash
# 飞书应用凭证
LARK_APP_ID=cli_xxxxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxx

# 可选：飞书 CLI Token（如果使用 CLI 方式）
LARK_CLI_TOKEN=
```

---

## 5. 权限检查清单

在开发前，请确认：

- [ ] 已创建飞书应用
- [ ] 已开通所有必需权限
- [ ] 已开启机器人功能
- [ ] 已在测试环境配置 App ID 和 Secret
- [ ] 已在生产环境配置 App ID 和 Secret

---

## 6. 权限错误处理

### 6.1 常见错误

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| 99991672 | 权限不足 | 检查是否开通相应 scope |
| 99991400 | 参数错误 | 检查请求参数 |
| 99991403 | 未授权 | 检查 access_token 是否有效 |

### 6.2 调试建议

1. 使用飞书开放平台的「接口调试」工具
2. 检查应用的「权限管理」页面
3. 确认 access_token 是否包含正确的 scope

---

## 7. 安全建议

### 7.1 最小权限原则

- 只申请业务必需的权限
- 避免申请 `*` 通配符权限

### 7.2 凭证保护

- 不要将 `App Secret` 提交到代码仓库
- 使用环境变量或密钥管理服务
- 定期轮换访问凭证

### 7.3 权限隔离

- 不同环境使用不同的应用凭证
- 生产环境和测试环境权限分开管理

---

## 8. OpenClaw 权限配置

如果使用 OpenClaw 飞书插件，部分权限可能由 OpenClaw 统一管理：

```json
{
  "plugins": {
    "entries": {
      "knowledge-radar": {
        "enabled": true,
        "permissions": {
          "network": ["*"],
          "storage": ["read", "write"]
        }
      }
    }
  }
}
```

**待确认**:
- [ ] OpenClaw 是否提供权限申请的自动化？

---

## 9. 参考链接

- [飞书权限说明](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference)
- [权限范围一览](https://open.feishu.cn/document/home/index)
- [OAuth 2.0 鉴权](https://open.feishu.cn/document/server-docs/authentication-management-overview)

---

**最后更新**: 2024-05-01
