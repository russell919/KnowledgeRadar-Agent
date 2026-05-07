---
name: knowledge-radar
version: 2.1.0
description: "知识雷达：企业知识整合与分发Agent。支持五层流水线：知识整合 → 混合检索 → 场景理解 → 精准分发(PushScore) → 反馈沉淀"
metadata:
  requires:
    bins: ["lark-cli"]
---

# 知识雷达 Agent Skill v2.2

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md)，其中包含认证、权限处理**

## 核心架构

知识雷达 v2.2 采用**五层流水线架构**，每个场景的处理都贯穿完整链路：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        事件/请求入口                                     │
│  用户消息  │  飞书Webhook  │  定时任务 (cron)                            │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ① 知识整合层 (Knowledge Integration)                                    │
│                                                                         │
│  调用 knowledge_radar.ingest_event 摄入各来源数据 → 存储原始信息         │
│  后端自动执行：LLM/规则抽取实体&关系 → 生成知识项 → 索引到Hybrid Search │
│                                                                         │
│  来源：消息(im)、文档(doc)、日历(calendar)、任务(task)、表格(base)      │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ② 向量化 + 索引层 (Indexing) — 后端自动完成                            │
│                                                                         │
│           ┌──────────────┐      ┌─────────────────┐                    │
│           │ 语义通道       │      │ 关键词通道       │                    │
│           │ Embedding →   │      │ BM25 倒排索引   │                    │
│           │ TF-IDF 4096维 │      │ 中文分词支持     │                    │
│           └──────┬───────┘      └────────┬────────┘                    │
│                  │                       │                              │
│                  └───────────┬───────────┘                              │
│                              ▼                                          │
│                   Hybrid Search 引擎                                    │
│                   • 语义召回 (cosine similarity)                         │
│                   • 关键词召回 (BM25 score)                              │
│                   • 元数据过滤 (群聊/时间/类型)                          │
│                   • Reranker 重排 (交叉信号评分)                         │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ③ 场景理解层 — 由 Agent 编排 (THIS IS YOUR JOB)                        │
│                                                                         │
│  触发事件 → 场景识别 → 使用下述工具组合检索 → 知识需求清单              │
│                                                                         │
│  每个场景的知识需求清单（详见下文各场景工作流）：                         │
│  • MeetingBriefing: 上次决策 + 未闭环待办 + 风险 + 参会人画像          │
│  • WeeklyDigest:   高频主题 + 趋势 + 决策 + 风险 + 事件图               │
│  • DocChange:      变更摘要 + 影响范围 + 关联项目 + 相关人员            │
│  • Onboarding:     项目历史 + 必读文档 + 决策 + FAQ + 关键联系人       │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ④ 精准分发层 (PushScore) — 在 run_scene 输出中包含评分结果              │
│                                                                         │
│  PushScore = w1×角色相关性 + w2×项目参与度 + w3×任务责任度              │
│            + w4×时间紧迫性 + w5×信息新鲜度 + w6×已读状态               │
│            + w7×打扰成本                                                │
│                                                                         │
│  ≥0.8 → 立即推送  │  ≥0.5 → 定时摘要  │  ≥0.2 → 存档  │  <0.2 → 过滤  │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ⑤ 反馈沉淀层 (Feedback Loop) — Agent 应主动收集反馈                      │
│                                                                         │
│  推送后：提示用户反馈  →  调用 track_behavior 记录行为                   │
│                        →  调用 submit_feedback 提交反馈                  │
│  后端自动：更新用户画像 → 调整topic_interest → 影响PushScore            │
└─────────────────────────────────────────────────────────────────────────┘
```

## 可用工具一览（8 个 + 4 个 GraphRAG 动作）

| 工具 | 用途 | 使用场景 |
|------|------|---------|
| `knowledge_radar.run_scene` | 运行指定的知识雷达场景 | 主入口，覆盖全部4个场景 |
| `knowledge_radar.ingest_event` | 摄入外部事件到系统 | 知识整合：消息/文档/会议/任务 |
| `knowledge_radar.submit_feedback` | 提交用户反馈 | 推送后收集反馈，改进质量 |
| `knowledge_radar.preview_action` | 预览即将执行的动作 | 推送/修改前人工确认 |
| `knowledge_radar.admin_sync` | 执行数据同步 | 管理员手动同步数据源 |
| `knowledge_radar.track_behavior` | 记录用户行为事件 | 追踪用户交互，更新画像 |
| `knowledge_radar.search_knowledge` | 混合检索知识库 | 精细检索：将搜索词与场景结合 |
| `knowledge_radar.get_knowledge_graph` | 获取知识图谱关系 | 分析项目-人员-决策关联网络 |

**GraphRAG 分析**（通过 `search_knowledge` 配合 `get_knowledge_graph` 实现）：

| 分析模式 | 用途 | 适用场景 |
|---------|------|---------|
| 关系遍历 (traverse) | 沿实体关系边遍历，发现关联网络 | 文档影响分析、人员关联发现 |
| 上下文聚合 (context) | 为实体集合收集关联知识 | 会前简报补充关联决策/风险 |
| 影响分析 (impact) | 分析文档变更影响的项目/人/待办 | DocChange 精准推送 |
| 项目脉络 (project-overview) | 生成项目-人员-决策全景图 | Onboarding 新人入组包 |

---

## 四大场景完整工作流

### 场景 1：会前简报 (meeting_briefing)

**触发词**：会前简报、会议准备、会前30分钟、某某会议的简报

**工作流**：

```
Step 1: 调用 run_scene(sceneType="meeting_briefing", triggerId=会议ID)
        → 后端自动：查日历 → 获取参会人 → Hybrid Search（按会议主题+参会人检索）
        → Event Graph 追踪未闭环事件
        → PushScore 评分（高优先级给参会人）
        → 返回：Markdown 简报 + source_refs

Step 2: 如果简报中缺少某个参会人的个性化信息：
        调用 search_knowledge(query="张三 相关 任务", filter={type: "action_item"})
        调用 get_knowledge_graph(entityName="张三")
        补充到简报中

Step 3: 推送后，主动询问反馈：
        "这份会前简报对你有帮助吗？"
        如果用户回复，调用 track_behavior 或 submit_feedback
```

**输出样例**：
```
📋 会前简报 — 知识雷达项目周会
🕐 2026-05-06 15:00

📌 上次决策
- 确定采用 Hybrid Search 作为检索方案
- 决定 v2.2 使用 SQLite（无需 PostgreSQL）

📌 待闭环事项
- 王五：完成 FAQ 模块设计（ddl: 5/10）
- 张三：PRD 评审排期

⚠️ 当前风险
- 后端服务 QPS 可能不足

🔗 事件上下文
- 知识雷达项目：2个未闭环任务，1个已解决风险
```

---

### 场景 2：每周知识推送 (weekly_digest)

**触发词**：每周知识推送、周报摘要、知识汇总、本周动态

**工作流**：

```
Step 1: 调用 run_scene(sceneType="weekly_digest")
        → 后端自动：取本周知识项 + Hybrid Search + Event Graph 趋势
        → PushScore 给每个用户打分 → 只推给分数≥0.5的人
        → 返回：Markdown 周报 + 统计

Step 2: 如果有高频问题/反复讨论的话题：
        可调用 search_knowledge(query="FAQ 问题", filter={type: "info"}, mode="keyword")
        看是否有沉淀候选

Step 3: 推送给用户后，主动收集反馈：
        "这周的知识推送对你有帮助吗？"
        收到回复后 → track_behavior(tracking)
```

**输出样例**：
```
📊 每周知识汇报

📄 本周知识条目（12条）
- [decision] 采用 Hybrid Search 方案
- [risk] 后端QPS瓶颈待优化
- [action_item] 完成FAQ模块设计

📌 本周决策（3项）
...

⚠️ 风险（2项）
...

🔄 事件趋势
- 知识雷达项目：5件本周活跃事件
  • 确定了 v2.2 架构
  • 完成 PushScore 合入
```

---

### 场景 3：新人入职引导 (onboarding)

**触发词**：新人入职、新人入组、onboarding、新同事入群

**工作流**：

```
Step 1: 调用 run_scene(sceneType="onboarding", triggerId=新人ID, 
                        params={userName: "姓名", roleTags: ["developer"]})
        → 后端自动：Hybrid Search 按角色检索相关文档 + Event Graph 项目脉络
        → 生成入组包（项目概览 + 必读材料 + 决策 + 风险 + 关键联系人）

Step 2: 通过 get_knowledge_graph 深入了解项目-人员关系：
        调用 get_knowledge_graph(entityName="具体项目名称")
        为新人制作更丰富的团队脉络图

Step 3: 检查是否有 FAQ：
        search_knowledge(query="常见问题 项目名", mode="hybrid")
        如果有，打包进 FAQ 卡片

Step 4: 推送后提醒新人反馈：
        "欢迎入组！如果有问题随时在群里提问，我们会持续更新入组包。"
        如需跟踪新人后续行为，调用 track_behavior
```

**输出样例**：
```
👋 欢迎入组！

📌 项目概览
当前项目：知识雷达Agent、积分调度系统

📄 必读材料
1. 知识雷达架构文档
2. PushScore 设计文档
3. 飞书 OpenAPI 接入指南

📌 关键决策
- 采用 Hybrid Search 检索方案
- 使用 SQLite 数据库

👥 关键联系人
- 王五（后端技术Lead）
- 张三（产品经理）
- 李四（架构师）

💡 常见问题
Q: 如何接入新数据源？
A: 调用 ingest_event 接口...
```

---

### 场景 4：文档变更提醒 (doc_change)

**触发词**：文档变更、重要更新、文档变化提醒、某某文档更新了

**工作流**：

```
Step 1: 调用 run_scene(sceneType="doc_change", triggerId=文档ID)
        → 后端自动：查飞书文档 → 变更内容摘要 → Event Graph 分析影响范围
        → PushScore 只推给相关人（协作人 + 项目成员 + 引用人）

Step 2: 分析影响：
        调用 get_knowledge_graph(entityName="文档标题")
        查看哪些项目和人引用了该文档

Step 3: 如果需要精确搜索变更附带的知识：
        search_knowledge(query="文档标题 + 关键词", filter={sinceDays: 7})

Step 4: 推送后收集反馈：
        调用 track_behavior(userId=xx, type="read", knowledgeId=xx)
```

**输出样例**：
```
📝 文档更新提醒

文档：知识雷达架构设计 v2.2
作者：张三
更新时间：2026-05-06 14:30

变更摘要：
- 新增：Feedback Loop 章节
- 修改：检索层从单通道改为三通道（语义+关键词+重排）
- 删除：SQLite 扩展章节（已迁移到独立文档）

影响范围：
- 📌 知识雷达项目（项目成员：5人）
- 📌 后端架构评审（关联决策1项）
- 📋 张三的待办：完成FAQ模块实现（关联此项变更）
```

---

## 通用工作流模板（Agent 编排规范）

### 标准处理流程

Agent 在收到任何知识雷达请求时，应按以下顺序处理：

```
1. 场景识别：根据用户消息判断场景类型
2. 主执行：调用 run_scene 获取核心输出
3. 精细化补充（可选）：
   - 如果输出缺少某个实体的信息 → get_knowledge_graph
   - 如果输出需要更多上下文 → search_knowledge
   - 如果需要预览再执行 → preview_action
4. 推送呈现：将 run_scene 的 Markdown 输出推送给用户
5. 反馈收集：在回复中附上反馈引导
6. 反馈记录：用户响应后 → track_behavior / submit_feedback
```

### 反馈收集规范

每次推送都必须包含反馈引导：

```
会前简报/周报/入组包/文档变更推送内容...

---

📊 你觉得这份[场景名称]对你有帮助吗？
   👍 有帮助 | 👎 没帮助 | ✏️ 提出问题
```

当用户回应后，根据回应调用：

- **有用/收藏** → `knowledge_radar.track_behavior(userId, type="collect", knowledgeId=execId)`
- **没帮助/忽略** → `knowledge_radar.submit_feedback(executionId, feedbackType="not_useful", content=原因)`
- **提出问题** → `knowledge_radar.track_behavior(userId, type="follow_up", content=问题)`

### Preview（人工确认）规范

以下场景必须先走预览再执行：

| 场景 | 需要 preview 的条件 |
|------|-------------------|
| 每周推送 | 推送给 ≥3 人时 |
| 文档变更 | ✅ 每次都需要 |
| 新人入职 | ✅ 每次都需要 |
| 会前简报 | 推送给 ≥5 人时 |
| 数据同步 | ✅ admin_sync 前需要 |
| 写入知识库 | ✅ 任何修改都需要 |

**注意**：`run_scene` 的 `dryRun=true` 模式可以直接返回预览内容，不需额外调用 `preview_action`。仅在 `run_scene` 没有 dryRun 参数或需要查看特定动作时才用 `preview_action`。

---

## 工具详细说明

### 1. knowledge_radar.run_scene

**核心工具**。覆盖全部 4 个场景。大多数情况下 Agent 只需调用这一个工具即可完成场景处理。

**关键参数**：

| 参数 | 必填 | 说明 |
|------|------|------|
| `sceneType` | 是 | `weekly_digest` / `meeting_briefing` / `doc_change` / `onboarding` |
| `triggerId` | 否 | 触发源ID（会议ID/文档ID/新人ID） |
| `params` | 否 | `{userName, roleTags, participants, title, description, startTs, endTs}` 等场景特定参数 |
| `dryRun` | 否 | `true` 为预览模式，不实际推送 |

**params 详细说明**（按场景）：

```
meeting_briefing:
  { title: "会议标题", participants: ["用户A", "用户B"], description: "会议描述",
    startTs: <unix时间戳-开始>, endTs: <unix时间戳-结束> }

weekly_digest:
  {}  # 一般来说不需要额外参数

doc_change:
  { title: "文档标题/搜索关键词" }

onboarding:
  { userName: "新人姓名", roleTags: ["developer", "pm", "designer"] }
```

**输出包含**：
- `executionId` — 用于后续反馈追踪
- `summary` — Markdown 格式的推送内容
- `preview` — `dryRun=true` 时的预览内容
- `sourceRefs` — 信息引用来源列表
- `stats` — 推送统计

### 2. knowledge_radar.search_knowledge

**精细检索工具**。当 `run_scene` 的输出不足，或需要具体查询某方面的知识时使用。

**典型用法**：

```javascript
// 按场景检索
search_knowledge({ query: "积分调度系统 风险评估",
  mode: "hybrid", topK: 10,
  filter: { type: "risk", sinceDays: 30 } })

// 精确关键词检索
search_knowledge({ query: "FAQ 接入指南",
  mode: "keyword", topK: 5 })

// 按时间段 + 实体检索
search_knowledge({ query: "知识雷达 v2",
  filter: { entities: ["张三", "王五"], sinceDays: 14 } })
```

### 3. knowledge_radar.get_knowledge_graph

**关系分析工具**。查看项目-人员-决策的关系网络。

**典型用法**：

```javascript
// 查看某人的关联网络
get_knowledge_graph({ entityName: "张三" })

// 查看某项目的关联网络
get_knowledge_graph({ entityName: "知识雷达" })
```

### 4. knowledge_radar.ingest_event

**知识摄入工具**。将外部事件输入知识雷达系统。

**典型用法**：

```javascript
// 摄入一条消息
ingest_event({
  eventType: "message",
  sourceId: "msg_xxx",
  sourceType: "im",
  data: { content: "...", sender: "张三", chat_id: "..." }
})

// 摄入文档更新
ingest_event({
  eventType: "document_updated",
  sourceId: "doc_xxx",
  sourceType: "doc",
  data: { title: "...", content: "...", author: "..." }
})
```

### 5. knowledge_radar.track_behavior

**行为追踪工具**。记录用户行为以更新画像和优化推送。

**典型用法**：

```javascript
// 用户点击了推送内容
track_behavior({ userId: "user_xxx", type: "click",
  knowledgeId: "k_xxx" })

// 用户追问了某个话题
track_behavior({ userId: "user_xxx", type: "follow_up",
  content: "请详细介绍 Hybrid Search 的实现细节" })

// 用户搜索了某个关键词
track_behavior({ userId: "user_xxx", type: "search",
  content: "PushScore 权重配置" })
```

### 6. knowledge_radar.submit_feedback

**反馈提交工具**。用于用户明确表达对推送内容的评价。

**典型用法**：

```javascript
submit_feedback({
  executionId: "exec_xxx",
  feedbackType: "not_useful",
  content: "这些决策我已经知道了，不需要重复推送",
  userId: "user_xxx"
})
```

### 7. knowledge_radar.preview_action

**动作预览工具**。在执行敏感操作前预览效果。

**典型用法**：

```javascript
preview_action({
  actionType: "push_content",
  params: { sceneType: "meeting_briefing", receivers: [...] }
})
```

### 8. knowledge_radar.admin_sync

**管理同步工具**。全量或增量同步数据源。

**典型用法**：

```javascript
admin_sync({ syncType: "incremental",
  sources: ["im", "doc", "calendar"],
  async: true })
```

---

## 使用约束

### ⚠️ 重要原则

1. **不要编造来源**：所有推送内容必须从 `run_scene` 返回的 `sourceRefs` 中获取真实来源，不能凭空生成

2. **preview 优先**：参照上述 Preview 规范，在需要人工确认时先预览

3. **权限过滤**：
   - `run_scene` 后端已处理权限（按聊天权限取最严原则）
   - 手动调用 `search_knowledge` 时注意不要越权

4. **反馈闭环**：每次推送都必须包含反馈引导，这是提升推送质量的关键

5. **dryRun 参数**：`run_scene(sceneType="xxx", dryRun=true)` 可以预览而不实际推送，推荐在首次运行新场景时先用 dryRun

### 场景触发速查

```
用户说"帮我生成会前简报"
→ run_scene(sceneType="meeting_briefing")

用户说"看看这周有什么重要更新"
→ run_scene(sceneType="weekly_digest")

用户说"新人入群了，帮他准备入组包"
→ run_scene(sceneType="onboarding", params={userName: "新人名", roleTags: [...]})

用户说"XX文档更新了，帮我看看"
→ run_scene(sceneType="doc_change", triggerId="文档ID")

用户说"帮我查一下这个项目的相关人员"
→ get_knowledge_graph(entityName="项目名")

用户说"搜索关于XX的知识"
→ search_knowledge(query="关键词", mode="hybrid")
```

---

## 参考

- [lark-shared](../lark-shared/SKILL.md) — 认证、权限（必读）
- 后端服务：http://127.0.0.1:8787
- 健康检查：`GET /v1/health`
