# Knowledge Radar Agent

企业知识整合与分发服务 - 基于 OpenClaw + 飞书/Lark 的智能 Agent

## 项目概述

Knowledge Radar Agent 是一个企业知识整合与分发系统，支持四个核心场景：

| 场景 | 说明 |
|------|------|
| `weekly_digest` | 每周知识推送 - 定期汇总本周重要知识、决策、进展 |
| `meeting_briefing` | 会前简报 - 会议开始前自动整理上次会议结论和相关文档更新 |
| `doc_change` | 文档变更提醒 - 监控关键文档变更，精准推送给受影响人员 |
| `onboarding` | 新人入职引导 - 新成员加入时自动生成入组包 |

## 目录结构

```
KnowledgeRadar-Agent-Trae/
├── apps/
│   └── knowledge-radar-agent/           # Python 后端服务
│       ├── src/knowledge_radar/
│       │   ├── main.py                  # FastAPI 应用入口
│       │   ├── config.py                # 配置管理
│       │   ├── logging_config.py        # 日志配置
│       │   ├── dependencies.py         # 依赖注入
│       │   └── api/                     # API 路由
│       │       ├── routes_health.py
│       │       ├── routes_run.py
│       │       ├── routes_ingest.py
│       │       ├── routes_feedback.py
│       │       └── routes_admin.py
│       ├── pyproject.toml
│       ├── Dockerfile
│       ├── .env.example
│       └── alembic.ini
├── extensions/
│   └── knowledge-radar/                 # OpenClaw 插件层
│       ├── src/
│       │   ├── index.ts                 # 插件入口
│       │   ├── config.ts
│       │   ├── http-client.ts
│       │   ├── types.ts
│       │   ├── commands.ts
│       │   └── tools/
│       └── skills/
│           └── knowledge-radar/
└── configs/
    └── knowledge-radar.example.json      # 配置文件示例
```

## 部署说明

### 前置要求

- Python 3.11+
- PostgreSQL 15+ (with pgvector extension)
- Redis 7+
- Node.js 20+ (for OpenClaw plugin)

### 移植步骤

**本项目设计为可移植到 OpenClaw 根目录：**

1. 将 `apps/knowledge-radar-agent/` 复制到 `<OPENCLAW_ROOT>/apps/knowledge-radar-agent/`
2. 将 `extensions/knowledge-radar/` 复制到 `<OPENCLAW_ROOT>/extensions/knowledge-radar/`
3. 将 `configs/knowledge-radar.example.json` 复制到 `<OPENCLAW_ROOT>/configs/`

### 安装依赖

```bash
cd apps/knowledge-radar-agent
pip install -e ".[dev]"
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

### 启动服务

**开发模式：**

```bash
uvicorn knowledge_radar.main:app --host 0.0.0.0 --port 8787 --reload
```

**生产模式：**

```bash
uvicorn knowledge_radar.main:app --host 0.0.0.0 --port 8787 --workers 4
```

### Docker 部署

```bash
docker build -t knowledge-radar-agent:latest -f Dockerfile ..
docker run -d -p 8787:8787 --env-file .env knowledge-radar-agent:latest
```

## API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/v1/health` | 健康检查 |
| `POST` | `/v1/run-scene` | 运行知识雷达场景 |
| `POST` | `/v1/ingest-event` | 摄入单个事件 |
| `POST` | `/v1/ingest-batch` | 批量摄入事件 |
| `POST` | `/v1/feedback` | 提交反馈 |
| `POST` | `/v1/admin/sync` | 数据同步 |
| `POST` | `/v1/admin/seed-demo` | 填充演示数据 |
| `POST` | `/v1/admin/rebuild-index` | 重建索引 |
| `POST` | `/v1/preview-action` | 动作预览 |

## 配置说明

### OpenClaw 插件配置

在 OpenClaw 配置文件中添加：

```json
{
  "extensions": {
    "knowledge-radar": {
      "enabled": true,
      "config": {
        "backendBaseUrl": "http://localhost:8787",
        "enableHumanPreview": true
      }
    }
  }
}
```

### 飞书应用配置

需要在飞书开放平台创建应用，并配置：
- 权限范围
- 事件订阅
- 获取 App ID 和 App Secret

## 开发指南

### 代码规范

```bash
# 代码检查
ruff check .

# 代码格式化
ruff format .

# 类型检查
mypy src/
```

### 测试

```bash
pytest tests/ -v
```

## 移植说明

### 前置要求

- Python 3.11+
- Node.js 20+ (for OpenClaw plugin)
- Docker 和 Docker Compose (可选)

### 移植步骤

**本项目设计为可移植到 OpenClaw 根目录：**

1. 将 `apps/knowledge-radar-agent/` 复制到 `<OPENCLAW_ROOT>/apps/knowledge-radar-agent/`
2. 将 `extensions/knowledge-radar/` 复制到 `<OPENCLAW_ROOT>/extensions/knowledge-radar/`
3. 将 `configs/knowledge-radar.example.json` 复制到 `<OPENCLAW_ROOT>/configs/knowledge-radar.json`

### 本地启动

#### 1. 安装后端依赖

```bash
cd apps/knowledge-radar-agent
pip install -e ".[dev]"
```

#### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

#### 3. 启动依赖服务 (Docker)

```bash
docker-compose -f docker-compose.knowledge-radar.yml up -d
```

#### 4. 导入演示数据

```bash
cd apps/knowledge-radar-agent
python -m knowledge_radar.demo.seed_demo_data
```

#### 5. 启动后端服务

```bash
# 开发模式
uvicorn knowledge_radar.main:app --host 0.0.0.0 --port 8787 --reload

# 或生产模式
uvicorn knowledge_radar.main:app --host 0.0.0.0 --port 8787 --workers 4
```

#### 6. 编译并启用 OpenClaw 插件

```bash
cd <OPENCLAW_ROOT>/extensions/knowledge-radar
npm install
npm run build
```

### 触发四个 Demo

#### 每周知识推送 (weekly_digest)

```bash
curl -X POST http://localhost:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType": "weekly_digest", "workspaceId": "apollo-workspace"}'
```

#### 会前简报 (meeting_briefing)

```bash
curl -X POST http://localhost:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType": "meeting_briefing", "workspaceId": "apollo-workspace"}'
```

#### 文档变更提醒 (doc_change)

```bash
curl -X POST http://localhost:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType": "doc_change", "workspaceId": "apollo-workspace"}'
```

#### 新人入职引导 (onboarding)

```bash
curl -X POST http://localhost:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType": "onboarding", "workspaceId": "apollo-workspace", "params": {"newUserId": "new-user"}}'
```

### 回滚步骤

1. 停止后端服务：

```bash
pkill -f "uvicorn knowledge_radar"
```

2. 停止 Docker 服务：

```bash
docker-compose -f docker-compose.knowledge-radar.yml down
```

3. 移除插件（可选）：

```bash
rm -rf <OPENCLAW_ROOT>/extensions/knowledge-radar
rm -rf <OPENCLAW_ROOT>/apps/knowledge-radar-agent
```

### 运行测试

```bash
cd apps/knowledge-radar-agent
pytest tests/ -v
```

## 文档

- [INTEGRATION_GAPS.md](docs/INTEGRATION_GAPS.md) - 集成缺口清单
- [FEISHU_PERMISSIONS.md](docs/FEISHU_PERMISSIONS.md) - 飞书权限配置
- [OPENCLAW_INSTALL.md](docs/OPENCLAW_INSTALL.md) - OpenClaw 安装指南

## License

MIT
