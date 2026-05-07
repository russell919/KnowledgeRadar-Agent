# 知识雷达 Agent · KnowledgeRadar Agent

> **企业办公知识整合与分发智能体**
>
> 五层流水线：知识整合 → 混合检索 → 场景理解 → 精准分发(PushScore) → 反馈沉淀

---

## 项目简介

知识雷达 Agent 是一个面向飞书/企业办公场景的知识管理智能体，解决企业知识分散、重复查找成本高、关键信息难以触达的问题。

### 核心能力

| 场景 | 功能 | 技术实现 |
|------|------|---------|
| **会前简报** | 会前 30 分钟自动生成结构化摘要 | Hybrid Search + GraphRAG + PushScore |
| **每周推送** | 本周高频主题聚类 + 个人相关决策分层推送 | Embedding 聚类 + PushScore + FAQ 沉淀 |
| **新人入职** | Day 1-7 逐日推送 + 项目全景脉络 | GraphRAG 遍历 + 权限过滤 + Onboarding 推送器 |
| **文档变更** | 变更摘要 + 影响范围分析 + 版本回溯 | 语义 diff + GraphRAG 影响分析 |

### 技术栈

- **平台**: [OpenClaw](https://openclaw.ai) — 智能体运行时
- **后端**: Node.js — 纯 JS 实现
- **存储**: SQLite (via sql.js) — 零数据库服务依赖
- **Embedding**: 字符级 n-gram TF-IDF（4096 维，纯 JS）
- **检索**: Hybrid Search（语义 + BM25 + 时效 + 权威四维融合）
- **增强**: GraphRAG（BFS 加权遍历实体关系图）
- **分发**: PushScore（7 维评分模型，四档门限决策）
- **LLM**: DeepSeek-v4-Flash（场景摘要 / NL2SQL / FAQ 提炼）

---

## 目录结构

```
KnowledgeRadar-Agent-V1.0/
├── backend-server/           # Node.js 后端服务器
│   ├── server.js             # 主入口（22 个 API 端点）
│   ├── database.js           # SQLite 数据库层（15 张表）
│   ├── embedding.js          # 中文 Embedding（字符级 n-gram TF-IDF）
│   ├── bm25.js               # BM25 倒排索引引擎
│   ├── hybrid-search.js      # Hybrid Search 多策略融合检索
│   ├── reranker.js           # Reranker 重排器
│   ├── graphrag.js           # 轻量 GraphRAG 关系增强
│   ├── event-graph.js        # 事件链追踪
│   ├── push-score.js         # PushScore 7 维分发评分
│   ├── executors.js          # 4 个场景执行器
│   ├── behavior-tracker.js   # 用户行为追踪
│   ├── faq-miner.js          # FAQ 自动沉淀
│   ├── chunker.js            # 文档语义切分
│   ├── text-to-sql.js        # 自然语言转 SQL
│   ├── onboarding-push.js    # 新人入职 Day1-7 推送
│   ├── batch-processor.js    # 批量事件处理器
│   ├── llm-client.js         # DeepSeek LLM 客户端
│   ├── feishu-client.js      # 飞书 Open API 客户端
│   ├── package.json          # Node.js 依赖声明
│   ├── .env.example          # 环境变量模板
│   ├── start.sh              # 启动脚本
│   └── knowledge.db          # 运行态数据库
│
├── extensions/
│   ├── knowledge-radar/      # OpenClaw 插件（TypeScript 源码 + 编译输出）
│   │   ├── src/tools/        # 8 个 Agent Tool
│   │   │   ├── ingest-event.ts       # 事件导入
│   │   │   ├── run-scene.ts          # 场景执行
│   │   │   ├── search-knowledge.ts   # 知识检索
│   │   │   ├── knowledge-graph.ts    # 知识图谱
│   │   │   ├── submit-feedback.ts    # 反馈提交
│   │   │   ├── track-behavior.ts     # 行为追踪
│   │   │   ├── preview-action.ts     # 操作预览
│   │   │   └── admin-sync.ts         # 管理同步
│   │   ├── dist/             # 编译后的 JS 文件
│   │   ├── skills/           # SKILL.md 工作流定义
│   │   └── openclaw.plugin.json
│   └── lark-shared/          # 飞书共享技能
│       └── skills/lark-shared/SKILL.md
│
├── configs/
│   └── knowledge-radar.example.json  # 插件配置模板
│
├── memory/                   # 运行态记忆文件（用于 Agent 上下文恢复）
│
├── archive/                  # 历史代码归档
│
├── java-demo/                # Java SDK Demo（飞书 Open API 调用示例）
│
├── DEMO_PLAN.md              # Demo 计划说明
└── .gitignore
```

---

## 部署方法

### 前置要求

- Node.js ≥ 18.x
- [OpenClaw](https://openclaw.ai) 已安装并配置（版本 ≥ 2026.4.26）
- 飞书自建应用（用于获取 API Token，可选）

### 第一步：启动后端服务器

```bash
# 1. 进入后端目录
cd backend-server

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的飞书 FEISHU_TOKEN

# 3. 安装依赖
npm install

# 4. 启动服务器
bash start.sh
# 默认监听 http://127.0.0.1:8787

# 验证运行状态：
curl http://127.0.0.1:8787/v1/health
# 预期返回: {"success":true,"status":"ok","timestamp":"..."}
```

### 第二步：安装 OpenClaw 插件

```bash
# 将 extensions/knowledge-radar 复制到 OpenClaw 目录：
cp -r extensions/knowledge-radar /path/to/openclaw/extensions/

# 编辑 openclaw.json，在 plugins.entries 中添加：
{
  "knowledge-radar": {
    "enabled": true,
    "config": {
      "backendBaseUrl": "http://localhost:8787"
    }
  }
}

# 重启 OpenClaw gateway：
openclaw gateway restart
```

> **注**：`dist/` 目录已包含编译后的 JS 文件，可直接使用。如需修改源码后重新编译：`cd extensions/knowledge-radar && npm install && npm run build`

### 第三步：配置插件

```bash
# 插件配置项说明（configs/knowledge-radar.example.json）：
{
  "backendBaseUrl": "http://localhost:8787",  # 后端服务地址
  "apiKey": "your-api-key",                   # API 密钥（可选）
  "defaultWorkspaceId": "apollo-workspace",   # 默认工作空间
  "enableHumanPreview": true                  # 推送前人工预览
}
```

---

## API 文档

后端提供 22 个 HTTP API 端点：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/v1/health` | GET | 健康检查 |
| `/v1/ingest-event` | POST | 导入事件 |
| `/v1/run-scene` | POST | 执行场景 |
| `/v1/knowledge/search` | POST | Hybrid Search 知识检索 |
| `/v1/knowledge/entity` | GET | 查询实体 |
| `/v1/knowledge/relation` | GET | 查询关系 |
| `/v1/knowledge/graph` | POST | GraphRAG 图谱遍历 |
| `/v1/knowledge/impact` | GET | 变更影响分析 |
| `/v1/knowledge/meetings/upcoming` | GET | 获取即将开始的会议 |
| `/v1/user/profile` | GET/POST | 用户画像管理 |
| `/v1/user/behavior` | POST | 记录用户行为 |
| `/v1/feedback/submit` | POST | 提交反馈 |
| `/v1/faq/mine` | POST | 触发 FAQ 挖掘 |
| `/v1/faq/list` | GET | 获取 FAQ 候选 |
| `/v1/faq/review` | POST | 审核 FAQ |
| `/v1/document/chunk` | POST | 文档分块 |
| `/v1/document/versions` | GET | 文档版本历史 |
| `/v1/nl2sql` | POST | 自然语言转 SQL |
| `/v1/admin/sync` | POST | 管理同步 |
| `/v1/feishu/webhook` | POST | 飞书 Webhook 接收 |
| `/v1/status` | GET | 系统状态 |
| `/v1/stats` | GET | 统计信息 |

### 快速测试：生成会前简报

```bash
curl -X POST http://127.0.0.1:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType":"meeting_briefing","triggerId":"test-001"}'
```

---

## 运行验证

启动后端后，可通过以下命令验证核心功能：

```bash
# Embedding 相似度验证
curl -X POST http://127.0.0.1:8787/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query":"微服务架构"}'

# 应返回语义相近的知识条目，按 Hybrid Search 分数排序

# 系统状态
curl http://127.0.0.1:8787/v1/status

# 预期返回类似：
# {
#   "entityCount": 107,
#   "relationCount": 100,
#   "knowledgeCount": 38,
#   ...
# }
```

---

## 许可

MIT License
