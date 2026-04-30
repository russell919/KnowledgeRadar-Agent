---
name: knowledge-radar
version: 1.0.0
description: "知识雷达：企业知识整合与分发Agent。支持四个核心场景：每周知识推送(weekly_digest)、会前30分钟简报(meeting_briefing)、关键文档变更提醒(doc_change)、新人入职引导(onboarding)。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# 知识雷达 Agent Skill

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../lark-shared/SKILL.md`](../../lark-shared/SKILL.md)，其中包含认证、权限处理**

## 核心定位

知识雷达是一个企业知识整合与分发Agent，基于OpenClaw + 飞书/Lark实现。它的核心能力不是简单回答问题，而是：

1. **知识整合**：将分散在文档、群聊、会议纪要、任务、多维表格中的信息统一入库
2. **场景理解**：根据触发事件判断当前办公场景
3. **精准分发**：结合权限、用户画像、知识重要性、反打扰策略决定推送对象和内容
4. **持续沉淀**：根据反馈更新用户画像，把高频知识沉淀为FAQ/SOP/项目记忆

## 四大核心场景

| 用户请求 | 场景类型 | 说明 |
|---------|---------|------|
| "每周知识推送"、"周报摘要"、"知识汇总" | `weekly_digest` | 定期汇总本周重要知识、决策、进展，推送给相关人员 |
| "会前简报"、"会议准备"、"会前30分钟" | `meeting_briefing` | 会议开始前自动整理上次会议结论、未闭环待办、相关文档更新 |
| "文档变更"、"重要更新"、"文档变化提醒" | `doc_change` | 监控关键文档变更，精准推送给受影响的人员 |
| "新人入职"、"新人入组"、"onboarding" | `onboarding` | 新成员加入时，自动生成入组包，包含项目介绍、关键联系人、必读材料 |

## 工具清单

### 1. knowledge_radar.run_scene
**功能**：运行指定的知识雷达场景

**输入参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sceneType` | string | 是 | 场景类型：`weekly_digest` \| `meeting_briefing` \| `doc_change` \| `onboarding` \| `manual` |
| `triggerId` | string | 否 | 触发源ID，如会议ID、文档ID |
| `workspaceId` | string | 否 | 工作空间ID |
| `params` | object | 否 | 自定义参数 |
| `dryRun` | boolean | 否 | 是否预览模式（不实际推送），默认false |

**输出**：
```json
{
  "success": true,
  "executionId": "exec_xxx",
  "summary": "已为3位用户生成会前简报",
  "preview": {...},  // dryRun模式下返回
  "stats": {...},
  "sourceRefs": [...]
}
```

### 2. knowledge_radar.ingest_event
**功能**：摄入外部事件到知识雷达系统

**输入参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `eventType` | string | 是 | 事件类型：`message` \| `document_updated` \| `document_created` \| `meeting_ended` \| `task_updated` \| `user_joined` \| `custom` |
| `sourceId` | string | 是 | 事件源ID |
| `sourceType` | string | 是 | 源类型：`im` \| `doc` \| `calendar` \| `task` \| `base` \| `wiki` \| `mail` |
| `data` | object | 是 | 事件数据 |
| `eventTime` | string | 否 | 事件时间（ISO 8601） |
| `workspaceId` | string | 否 | 工作空间ID |

**输出**：
```json
{
  "success": true,
  "eventId": "evt_xxx",
  "status": "completed",
  "message": "事件处理完成"
}
```

### 3. knowledge_radar.submit_feedback
**功能**：提交用户对推送内容的反馈

**输入参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `executionId` | string | 是 | 关联的执行ID |
| `feedbackType` | string | 是 | 反馈类型：`useful` \| `not_useful` \| `incorrect` \| `other` |
| `content` | string | 是 | 反馈内容 |
| `userId` | string | 否 | 用户ID |
| `metadata` | object | 否 | 额外元数据 |

**输出**：
```json
{
  "success": true,
  "feedbackId": "fb_xxx",
  "message": "感谢您的反馈"
}
```

### 4. knowledge_radar.preview_action
**功能**：预览即将执行的动作，用于人工确认

**输入参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `actionType` | string | 是 | 动作类型：`push_content` \| `update_knowledge` \| `sync_data` \| `send_notification` |
| `params` | object | 是 | 动作参数 |
| `workspaceId` | string | 否 | 工作空间ID |

**输出**：
```json
{
  "allowed": true,
  "preview": {
    "title": "即将推送：项目周报摘要",
    "description": "将推送给5位项目成员",
    "impactScope": "5人",
    "estimatedEffect": "提升团队信息同步效率"
  },
  "executionParams": {...},
  "warnings": ["部分成员可能处于免打扰模式"]
}
```

### 5. knowledge_radar.admin_sync
**功能**：执行管理员级别的数据同步

**输入参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `syncType` | string | 是 | 同步类型：`full` \| `incremental` |
| `sources` | array | 否 | 数据源列表 |
| `startTime` | string | 否 | 增量同步开始时间 |
| `workspaceId` | string | 否 | 工作空间ID |
| `async` | boolean | 否 | 是否异步执行，默认true |

**输出**：
```json
{
  "success": true,
  "taskId": "task_xxx",
  "status": "queued",
  "stats": {
    "totalItems": 0,
    "processedItems": 0,
    "failedItems": 0
  }
}
```

## 使用约束

### ⚠️ 重要原则

1. **不要编造来源**：所有推送内容必须携带`sourceRefs`，必须调用`knowledge_radar.run_scene`获取真实知识，不能凭空生成

2. **preview优先**：以下场景必须先走`preview_action`，等用户确认后再执行：
   - 广泛推送（推送给多个用户）
   - 写入知识库（修改/创建文档）
   - 关键变更推送（影响范围较大的更新）

3. **权限过滤**：在展示检索结果或执行推送前，必须确认当前用户有权限访问相关内容

4. **dryRun模式**：在正式环境中，建议先用`dryRun=true`预览效果，确认无误后再执行实际推送

## 场景触发示例

```
用户：帮我生成会前简报
-> 调用 knowledge_radar.run_scene(sceneType="meeting_briefing")

用户：看看有哪些新文档更新
-> 调用 knowledge_radar.run_scene(sceneType="doc_change")

用户：给新人发入组欢迎包
-> 调用 knowledge_radar.run_scene(sceneType="onboarding")

用户：这周有什么重要知识需要关注
-> 调用 knowledge_radar.run_scene(sceneType="weekly_digest")
```

## 权限表

| 命令 | 所需 scope |
|------|-----------|
| `knowledge_radar.run_scene` | 由后端控制 |
| `knowledge_radar.ingest_event` | 由后端控制 |
| `knowledge_radar.submit_feedback` | 由后端控制 |
| `knowledge_radar.preview_action` | 由后端控制 |
| `knowledge_radar.admin_sync` | 由后端控制 |

## 参考

- [lark-shared](../lark-shared/SKILL.md) — 认证、权限（必读）
- [lark-im](../lark-im/SKILL.md) — 消息相关操作
- [lark-doc](../lark-doc/SKILL.md) — 文档相关操作
- [lark-calendar](../lark-calendar/SKILL.md) — 日历相关操作
