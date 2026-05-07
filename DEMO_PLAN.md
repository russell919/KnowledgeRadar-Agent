# 《知识雷达 Agent》竞赛展示方案

**项目**：飞书 OpenClaw 赛道 — 企业办公知识整合与分发 Agent
**当前系统状态**：已完整实现全部 3 个阶段、22 个 API 端点、15 张数据库表
**版本**：v2.2.0

---

## 一、展示总纲（建议 8-10 分钟）

| 部分 | 时长 | 内容 |
|------|------|------|
| 痛点与愿景 | 1.5 min | 企业知识分散的四个典型困境 |
| 架构总览 | 1 min | 五层流水线一次看全 |
| **Demo 1：新人入组引导** | 1.5 min | 从入群到 7 天持续推送 |
| **Demo 2：会前简报** | 1.5 min | 开会有准备，决策不落地 |
| **Demo 3：每周知识汇报** | 1 min | 团队周报自动化 |
| **Demo 4：文档变更+FAQ** | 1.5 min | 变更即通知，问答自沉淀 |
| 技术亮点 | 1 min | 零 Python/PostgreSQL 依赖 |
| 结尾 | 0.5 min | 一句话总结 |

---

## 二、开场：痛点与愿景（1.5 min）

### 四个典型场景，评委一秒带入

> **友进**："想象一下这个周一早上——"
>
> - **场景 A**：新人小王加入项目群，不知道自己该读什么文档，也不知谁负责什么，第一周全是瞎摸
> - **场景 B**：你 10 分钟后要开会，但上次讨论了什么？谁负责什么？现在卡在哪？完全记不清
> - **场景 C**：团队群里每天几百条消息，张三点了个"好的"你没看见，需求变了你也不知道
> - **场景 D**：新同事问"怎么接入飞书文档？"，张老师回答了 3 遍了，但没人记下来

### 一句话价值

> **《知识雷达 Agent》**—— 就像给每个团队配了一个**永不掉线的知识管家**。消息自动沉淀、会议自动备菜、新人自动引导、变更自动通知。**知识找人，不是人找知识。**

---

## 三、架构总览（1 min）⭐

### 五层流水线 — 从收到推，一次看全

```
事件入口 ──→ ①知识整合 ──→ ②混合检索 ──→ ③场景理解 ──→ ④精准分发 ──→ ⑤反馈沉淀
                                              │
                                         四场景引擎
                                    ┌─────┼─────┬─────┐
                                  Onboard Brief  Digest Change
```

**展示方式**：直接投屏终端或 PPT 展示这个流水线图，同时口播。

> **关键数字**（现场展示）：`curl http://127.0.0.1:8787/v1/health`
> - 22 个 API 端点 | 15 张表 | 消息 + 实体 + 知识三位一体
> - Hybrid Search、GraphRAG、PushScore、FAQ 四引擎同时运行

---

## 四、Demo 1：新人入组引导（1.5 min）⭐ 开场必看

### 触发方式

```bash
curl -s -X POST http://127.0.0.1:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType":"onboarding","params":{"userId":"demo_new","userName":"实习生小王","roleTags":["intern","backend"],"projectName":"知识雷达"}}'
```

### 现场演示步骤

| 步骤 | 操作 | 屏幕效果 |
|------|------|---------|
| ① | 执行命令 | 终端返回长 Markdown |
| ② | 展示输出 | 指向 **项目概览** — GraphRAG 自动生成了 6 个实体节点、1 个相关人员 |
| ③ | 展示输出 | 指向 **关键决策** — Hybrid Search 找到了"采用微服务架构方案" |
| ④ | 展示输出 | 指向 **风险提示** — "数据库迁移方案存在风险" |
| ⑤ | 展示输出 | 指向 **关键联系人** — 按关联度排序 |

### 口播脚本

> "新人加入项目群，输入一条命令。系统做了什么？
>
> **第一**，Hybrid Search 根据新人角色标签 `intern+backend` + 项目名`知识雷达` 检索出最相关的文档和决策。**不是随便取 5 篇，而是按语义相关度排序。**
>
> **第二**，GraphRAG 沿实体关系网络遍历，找到了项目-人员-决策的全景图——小王还没开口，就知道谁是关键联系人。
>
> **第三**，7 天每日推送计划已经启动——明天推关键决策，后天推待办，以此类推。"

---

## 五、Demo 2：会前简报（1.5 min）⭐ 高实用

### 触发方式

```bash
curl -s -X POST http://127.0.0.1:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType":"meeting_briefing","params":{"title":"技术架构评审会","participants":[{"name":"张三"},{"name":"李四"}]}}'
```

### 现场演示步骤

| 步骤 | 操作 | 屏幕效果 |
|------|------|---------|
| ① | 执行 command | 返回会议简报 |
| ② | 指向摘要 | LLM 生成的上下文感知摘要 |
| ③ | 指向决策 | Hybrid Search 找到"采用微服务架构方案" |
| ④ | 指向待办 | Event Graph 追踪到"认证模块开发"未闭环 |
| ⑤ | 指向风险 | "数据库迁移方案存在风险" |

### 口播脚本

> "会议前 10 分钟，输入一条命令。
>
> LLM 生成了上下文摘要：'本次评审会参与者为张三和李四。**上次会议已决定采用微服务架构方案，但认证模块开发仍处于待办状态**。'
>
> 这句话不是模板拼接——**Hybrid Search 用'张三+李四+技术架构'做语义检索，Event Graph 追踪事件链发现未闭环待办，GraphRAG 补充关联风险。**三条线融合成一段人话。"

---

## 六、Demo 3：文档变更与 FAQ 沉淀（1.5 min）⭐ 闭环展示

### 6.1 文档语义切分

```bash
curl -s -X POST http://127.0.0.1:8787/v1/documents/chunk \
  -H "Content-Type: application/json" \
  -d '{"doc_id":"arch_v2","doc_title":"知识雷达架构文档","content":"## 项目背景\n\n知识雷达是一个企业知识管理Agent。\n\n## 系统架构\n\n采用五层流水线架构...\n\n### 2.1 知识整合层\n\n接入飞书文档、消息、会议纪要...\n\n### 2.2 检索层\n\n使用 Hybrid Search..."}'
```

### 6.2 FAQ 挖掘

```bash
# 先展示 FAQ 挖掘结果
curl -s -X POST http://127.0.0.1:8787/v1/faq/get -H 'Content-Type: application/json' -d '{}'
```

### 6.3 审核发布 FAQ

```bash
curl -s -X POST http://127.0.0.1:8787/v1/faq/review \
  -H 'Content-Type: application/json' \
  -d '{"faq_id":1,"action":"publish","answer":"微服务架构采用五层流水线设计..."}'
```

### 6.4 Text-to-SQL 全文检索

```bash
curl -s -X POST http://127.0.0.1:8787/v1/query/sql \
  -H 'Content-Type: application/json' \
  -d '{"query":"最近有哪些风险？"}'
```

### 口播脚本

> "文档更新后自动切分索引，FAQ 从聊天中自动挖掘，知识库可以自然语言查询——**不需要会 SQL，说人话就行**。'最近有哪些风险？' → 自动生成 SQL → 返回'4 项风险，包括数据库迁移方案风险……'"

---

## 七、Demo 4：批量消息处理（1 min）⭐ 展示工程能力

```bash
curl -s -X POST http://127.0.0.1:8787/v1/messages/process-batch \
  -H 'Content-Type: application/json' \
  -d '{"chatId":"oc_xxx","mode":"time","hours":24,"batchSize":50,"overlap":5}'
```

### 口播脚本

> "飞书群聊每天几百条消息，不可能一条一条手动摄入。
>
> **批量处理器**设计了两套策略：消息少的时候按时段一次处理，消息多的时候按 50 条一批，**批次间重叠 5 条保持上下文不割裂**。每批消息不仅逐条提取实体，**整批还会由 LLM 生成摘要**，自动沉淀进知识库。"

---

## 八、技术亮点（1 min）⭐ 展现硬实力

### 纯 Node.js 实现，零 Python/PostgreSQL 依赖

| 其他参赛方案 | 知识雷达 |
|-------------|---------|
| 需要 Python + PostgreSQL + pgvector | **纯 Node.js + SQLite，一条命令启动** |
| 依赖 GPU 做嵌入 | **字符级 n-gram TF-IDF（4096维），无 GPU 也能跑** |
| 依赖 HuggingFace 模型 | **纯 JS 实现 BM25 + 中文分词 + Reranker** |

### 核心创新点

1. **五层流水线设计**：知识整合 → 混合检索 → 场景理解 → 精准分发 → 反馈沉淀
2. **GraphRAG 轻量实现**：BFS 关系加权遍历，不走全量知识图谱
3. **PushScore 7 维评分**：角色相关性+项目参与度+任务责任度+时间紧迫性+信息新鲜度+已读状态+打扰成本
4. **Overlapping Batch Processing**：批次间重叠上下文，LLM 全批摘要

---

## 九、现场演示快速脚本

### 准备工作（Demo 前）

```bash
# 确保服务运行
ps aux | grep "node server"
# 健康检查
curl http://127.0.0.1:8787/v1/health
# 注入演示数据
curl -X POST http://127.0.0.1:8787/v1/ingest-event \
  -H 'Content-Type: application/json' \
  -d '{"event_id":"demo_1","event_type":"message","source_type":"im","data":{"content":"经过讨论决定采用微服务架构方案。认证模块由张三负责开发。","sender":"王五","chat_id":"demo_group"},"event_time":"2026-05-06T10:00:00Z"}'
```

### Demo 顺序（6 个命令，3 分钟）

```bash
# 1. Health — 开场展示数据
curl http://127.0.0.1:8787/v1/health

# 2. 新人入组 — 核心亮点
curl -X POST http://127.0.0.1:8787/v1/run-scene -H 'Content-Type: application/json' \
  -d '{"sceneType":"onboarding","params":{"userName":"小王","roleTags":["developer"],"projectName":"知识雷达"}}'

# 3. 会前简报 — 实用痛点
curl -X POST http://127.0.0.1:8787/v1/run-scene -H 'Content-Type: application/json' \
  -d '{"sceneType":"meeting_briefing","params":{"title":"架构评审会","participants":[{"name":"张三"}]}}'

# 4. 每周推送 — 自动化
curl -X POST http://127.0.0.1:8787/v1/run-scene -H 'Content-Type: application/json' \
  -d '{"sceneType":"weekly_digest"}'

# 5. FAQ 展示 — 知识沉淀
curl -X POST http://127.0.0.1:8787/v1/faq/get -H 'Content-Type: application/json' -d '{}'

# 6. Text-to-SQL — 自然语言查库
curl -X POST http://127.0.0.1:8787/v1/query/sql -H 'Content-Type: application/json' \
  -d '{"query":"有哪些风险？"}'
```

---

## 十、PPT / 录屏建议

### 推荐幻灯片结构（8-10 页）

| 页码 | 标题 | 内容 |
|------|------|------|
| 1 | 封面 | 知识雷达 Agent + 一句话 + 二维码 |
| 2 | 痛点 | 4 场景插画（新人/会议/周报/文档） |
| 3 | 架构 | 五层流水线图（Terminal 投屏匹配） |
| 4 | Demo1 | 新人入组：GraphRAG 项目脉络 |
| 5 | Demo2 | 会前简报：Hybrid Search + Event Graph |
| 6 | Demo3 | 文档变更 + FAQ + Text-to-SQL |
| 7 | Demo4 | 批量处理 + 上下文重叠 |
| 8 | 技术栈 | 纯 Node.js 技术亮点 |
| 9 | 结尾 | 一句话 + 联系方式 |

### 录屏建议

- 左半屏：终端黑底绿字（或 iTerm2 分屏）
- 右半屏：飞书界面（模拟推送效果）
- 每执行完一个命令，停 2-3 秒让评委看到输出
- 关键输出区域用**光标高亮**或**画框标注**（后期剪辑添加）

---

## 十一、评委可能问的问题

| 问题 | 回答要点 |
|------|---------|
| 跟 RAG 有什么区别？ | RAG 是单轮问答，知识雷达是**持续的闭环分发**，用 PushScore 决定推什么、推给谁、什么时候推，推送后还有反馈闭环 |
| 怎么保证知识质量？ | 置信度评分（LLM 0.7 vs 规则 0.4）+ FAQ 审核流程 + 用户反馈（负反馈自动降权） |
| 没有向量数据库怎么检索？ | 字符级 n-gram TF-IDF（4096维）+ BM25 双通道 + Reranker 重排。实测中文语义相似度识别正确 |
| 能做到实时吗？ | Webhook 事件是实时的，批量拉取是定时任务。混合架构：**实时消息即时处理，历史消息批量补全** |

---

## 总结一句话

> **知识雷达 = Hybrid Search 检索 + GraphRAG 关系增强 + PushScore 精准分发 + 反馈闭环持续进化。**
> **完全 Node.js，一行命令启动，开箱即用。**
