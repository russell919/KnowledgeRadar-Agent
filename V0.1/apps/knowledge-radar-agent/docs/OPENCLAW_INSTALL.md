# OpenClaw 插件安装指南

本文档描述如何将 Knowledge Radar 插件安装到 OpenClaw 环境。

---

## 1. 前置要求

### 1.1 系统要求

- Node.js 20+
- npm 或 yarn
- Python 3.11+
- PostgreSQL 15+ (with pgvector)
- Redis 7+

### 1.2 OpenClaw 环境

- OpenClaw 已安装并运行
- 管理员权限可以修改配置

---

## 2. 插件结构

Knowledge Radar 包含两部分：

```
KnowledgeRadar-Agent-Trae/
├── apps/
│   └── knowledge-radar-agent/           # Python 后端
├── extensions/
│   └── knowledge-radar/               # OpenClaw 插件
└── configs/
    └── knowledge-radar.example.json    # 配置文件
```

---

## 3. 安装步骤

### 3.1 复制文件

将以下目录复制到 OpenClaw 根目录：

```bash
# 复制 Python 后端到 OpenClaw apps 目录
cp -r apps/knowledge-radar-agent <OPENCLAW_ROOT>/apps/

# 复制插件到 OpenClaw extensions 目录
cp -r extensions/knowledge-radar <OPENCLAW_ROOT>/extensions/

# 复制配置文件
cp configs/knowledge-radar.example.json <OPENCLAW_ROOT>/configs/knowledge-radar.json
```

### 3.2 安装 Python 依赖

```bash
cd <OPENCLAW_ROOT>/apps/knowledge-radar-agent
pip install -e ".[dev]"
```

### 3.3 编译 TypeScript 插件

```bash
cd <OPENCLAW_ROOT>/extensions/knowledge-radar
npm install
npm run build
```

### 3.4 配置插件

编辑 `<OPENCLAW_ROOT>/configs/knowledge-radar.json`：

```json
{
  "extensions": {
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
```

### 3.5 配置 OpenClaw 主配置

在 OpenClaw 配置文件中添加：

```json
{
  "plugins": {
    "entries": {
      "knowledge-radar": {
        "enabled": true
      }
    }
  },
  "agents": {
    "defaults": {
      "skills": ["knowledge-radar"]
    }
  }
}
```

**待确认**:
- [ ] `agents.defaults.skills` 的正确格式
- [ ] 是否需要在 `plugins.entries` 中显式列出 skill 名称

---

## 4. 启动服务

### 4.1 启动后端

```bash
cd <OPENCLAW_ROOT>/apps/knowledge-radar-agent

# 开发模式
uvicorn knowledge_radar.main:app --host 0.0.0.0 --port 8787 --reload

# 生产模式
uvicorn knowledge_radar.main:app --host 0.0.0.0 --port 8787 --workers 4
```

### 4.2 启动 Worker (可选)

```bash
cd <OPENCLAW_ROOT>/apps/knowledge-radar-agent
celery -A knowledge_radar.workers.celery_app worker --loglevel=info
```

### 4.3 Docker Compose 启动

```bash
docker-compose -f docker-compose.knowledge-radar.yml up -d
```

---

## 5. 验证安装

### 5.1 检查后端健康

```bash
curl http://localhost:8787/v1/health
```

预期响应：
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 5.2 检查插件加载

在 OpenClaw 管理界面查看插件列表，确认「知识雷达」已启用。

### 5.3 测试 Skill

在 OpenClaw 对话框中输入：

```
@知识雷达 帮我生成会前简报
```

预期：返回会前简报或错误信息（如果后端未启动会返回连接错误）。

---

## 6. 触发四个 Demo 场景

### 6.1 每周知识推送 (weekly_digest)

```bash
# API 方式
curl -X POST http://localhost:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType": "weekly_digest", "workspaceId": "apollo-workspace"}'

# 或在 OpenClaw 中
@知识雷达 触发每周知识推送
```

### 6.2 会前简报 (meeting_briefing)

```bash
curl -X POST http://localhost:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType": "meeting_briefing", "workspaceId": "apollo-workspace"}'

# 或在 OpenClaw 中
@知识雷达 触发会前简报
```

### 6.3 文档变更提醒 (doc_change)

```bash
curl -X POST http://localhost:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType": "doc_change", "workspaceId": "apollo-workspace"}'

# 或在 OpenClaw 中
@知识雷达 触发文档变更提醒
```

### 6.4 新人入职引导 (onboarding)

```bash
curl -X POST http://localhost:8787/v1/run-scene \
  -H "Content-Type: application/json" \
  -d '{"sceneType": "onboarding", "workspaceId": "apollo-workspace", "params": {"newUserId": "new-user"}}'

# 或在 OpenClaw 中
@知识雷达 触发新人入职引导
```

---

## 7. 回滚步骤

### 7.1 停止服务

```bash
# 停止后端
pkill -f "uvicorn knowledge_radar"

# 停止 worker
pkill -f "celery.*knowledge_radar"

# 或使用 docker-compose
docker-compose -f docker-compose.knowledge-radar.yml down
```

### 7.2 移除插件

1. 在 OpenClaw 管理界面禁用「知识雷达」插件
2. 删除插件文件：

```bash
rm -rf <OPENCLAW_ROOT>/apps/knowledge-radar-agent
rm -rf <OPENCLAW_ROOT>/extensions/knowledge-radar
rm <OPENCLAW_ROOT>/configs/knowledge-radar.json
```

3. 重启 OpenClaw

### 7.3 清理数据库（可选）

如果需要完全清理：

```bash
docker-compose -f docker-compose.knowledge-radar.yml down -v
```

---

## 8. 常见问题

### 8.1 插件加载失败

**症状**: OpenClaw 启动时报插件加载错误

**排查**:
1. 检查 TypeScript 是否编译成功
2. 检查 `dist/index.js` 是否存在
3. 检查 `openclaw.plugin.json` 格式是否正确

### 8.2 后端连接失败

**症状**: 调用工具时报「无法连接到后端」

**排查**:
1. 检查后端是否运行：`curl http://localhost:8787/v1/health`
2. 检查 `backendBaseUrl` 配置是否正确
3. 检查防火墙是否放行 8787 端口

### 8.3 Skill 未生效

**症状**: 输入命令后 OpenClaw 无法识别

**排查**:
1. 检查 `agents.defaults.skills` 是否包含 `knowledge-radar`
2. 检查 OpenClaw 是否需要重启加载配置

---

## 9. 参考链接

- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw 官网](https://openclaw.ai/)
- [飞书开放平台](https://open.feishu.cn/)

---

**最后更新**: 2024-05-01
