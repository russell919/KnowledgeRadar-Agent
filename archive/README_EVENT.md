# 飞书事件监听脚本

实现了三个核心场景的实时事件监听与增量触发：
1. 新成员加入检测
2. 会议开始前30分钟提醒
3. 项目文档变更检测

## 前置准备

### 1. 认证登录
首先确保已经完成lark-cli认证：
```bash
lark-cli auth login
```

### 2. 应用权限配置
需要在飞书开放平台为你的应用开启以下事件权限：
- 通讯录事件：`contact.user.created_v2`（用户新增）
- 日历事件：`calendar.event.reminder`（日程提醒）
- 云文档事件：`doc.document.edit_v1`（文档编辑）
- 云空间事件：`drive.file.update_v1`（文件更新）

## 使用方法

### 直接运行脚本
```bash
python event_listener.py
```

### 后台运行（Windows）
```powershell
Start-Process python -ArgumentList "event_listener.py" -WindowStyle Hidden
```

## 功能说明

### 1. 新成员加入监听
- 实时接收新用户加入组织事件
- 自动去重，避免重复处理
- 存储新成员信息到本地数据库
- 支持扩展：自动发送欢迎消息、分配权限、同步到HR系统等

### 2. 会议30分钟提醒
- 过滤出提前30分钟的会议提醒事件
- 展示会议主题、时间、组织者、参会人、会议室等信息
- 支持扩展：自动发送提醒通知、准备会议材料、同步会议纪要模板等

### 3. 文档变更检测
- 同时监听云文档编辑和云空间文件更新事件
- 1分钟内的多次变更自动合并，避免重复触发
- 记录文档最后修改时间和修改人
- 支持扩展：通知项目组成员、自动同步备份、触发文档审核流程等

## 数据存储

脚本使用SQLite数据库`event_records.db`存储以下数据：
- `processed_events`：已处理事件记录，防止重复触发
- `user_records`：新加入成员记录
- `document_records`：文档变更记录

## 扩展自定义逻辑

在`event_listener.py`中找到对应处理器函数，添加你的业务逻辑：

```python
def handle_new_user(event: Dict):
    # 新成员加入时自动发送欢迎消息
    user_id = event.get("data", {}).get("object", {}).get("user_id", "")
    subprocess.run([
        "lark-cli", "im", "+send", 
        "--user-id", user_id, 
        "--text", "欢迎加入公司！请查看入职指南：xxx"
    ])
```

```python
def handle_document_change(event: Dict):
    # 文档变更时通知项目群
    doc_token = event.get("data", {}).get("object", {}).get("doc_token", "")
    doc_name = event.get("data", {}).get("object", {}).get("title", "")
    subprocess.run([
        "lark-cli", "im", "+send",
        "--chat-id", "项目群chat_id",
        "--text", f"文档【{doc_name}】已更新：https://bytedance.feishu.cn/doc/{doc_token}"
    ])
```

## 日志查看

运行日志会同时输出到控制台和`event_listener.log`文件：
```bash
# 查看最近日志
Get-Content event_listener.log -Tail 20
```

## 停止运行

如果前台运行，直接按`Ctrl+C`停止；如果后台运行，通过任务管理器结束python进程即可。
