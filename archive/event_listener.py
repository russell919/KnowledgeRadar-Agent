import json
import subprocess
import sqlite3
from datetime import datetime
from typing import Dict, Callable
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("event_listener.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

class EventListener:
    def __init__(self, db_path: str = "event_records.db"):
        self.db_path = db_path
        self.event_handlers: Dict[str, Callable] = {}
        self._init_db()

    def _init_db(self):
        """初始化数据库，存储已处理事件防止重复触发"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            processed_at TIMESTAMP NOT NULL,
            event_data TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_records (
            user_id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            join_time TIMESTAMP NOT NULL,
            department TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_records (
            doc_token TEXT PRIMARY KEY,
            doc_name TEXT NOT NULL,
            last_modified TIMESTAMP NOT NULL,
            last_modifier TEXT
        )
        """)
        
        conn.commit()
        conn.close()

    def is_event_processed(self, event_id: str) -> bool:
        """检查事件是否已经处理过"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_events WHERE event_id = ?", (event_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_event_processed(self, event_id: str, event_type: str, event_data: Dict):
        """标记事件为已处理"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO processed_events VALUES (?, ?, ?, ?)",
                (event_id, event_type, datetime.now(), json.dumps(event_data, ensure_ascii=False)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

    def register_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        self.event_handlers[event_type] = handler
        logger.info(f"注册事件处理器: {event_type}")

    def _parse_event_line(self, line: str) -> Dict:
        """解析lark-event输出的NDJSON行"""
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError:
            logger.warning(f"无法解析事件行: {line[:200]}")
            return {}

    def start(self, event_types: list):
        """启动事件监听"""
        event_types_str = ",".join(event_types)
        cmd = ["lark-cli", "event", "+subscribe", "--event-types", event_types_str, "--compact"]
        
        logger.info(f"启动事件监听，订阅事件: {event_types_str}")
        logger.info("按Ctrl+C停止监听")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8"
            )
            
            for line in iter(process.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                
                event = self._parse_event_line(line)
                if not event:
                    continue
                
                event_type = event.get("type", "")
                event_id = event.get("event_id", "")
                
                if not event_type or not event_id:
                    continue
                
                if self.is_event_processed(event_id):
                    logger.debug(f"事件已处理，跳过: {event_id} [{event_type}]")
                    continue
                
                logger.info(f"收到新事件: {event_type} (ID: {event_id[:8]}...)")
                
                handler = self.event_handlers.get(event_type)
                if handler:
                    try:
                        handler(event)
                        self.mark_event_processed(event_id, event_type, event)
                    except Exception as e:
                        logger.error(f"处理事件失败 {event_id}: {str(e)}", exc_info=True)
                else:
                    logger.debug(f"无对应处理器，跳过事件: {event_type}")
                    
        except KeyboardInterrupt:
            logger.info("停止事件监听")
            process.terminate()
        except Exception as e:
            logger.error(f"监听进程异常: {str(e)}", exc_info=True)

# 事件处理器实现
def handle_new_user(event: Dict):
    """处理新成员加入事件"""
    event_data = event.get("data", {})
    user = event_data.get("object", {})
    
    user_id = user.get("user_id", "")
    user_name = user.get("name", "")
    department = user.get("department_names", [])
    join_time = datetime.fromtimestamp(user.get("join_time", 0))
    
    logger.info(f"=== 新成员加入 ===")
    logger.info(f"姓名: {user_name}")
    logger.info(f"用户ID: {user_id}")
    logger.info(f"部门: {', '.join(department)}")
    logger.info(f"加入时间: {join_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 存储到数据库
    conn = sqlite3.connect("event_records.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO user_records VALUES (?, ?, ?, ?)",
            (user_id, user_name, join_time, ", ".join(department)),
        )
        conn.commit()
    finally:
        conn.close()
    
    # 这里可以添加自定义逻辑：发送欢迎消息、分配权限等
    # 示例: lark-cli im +send --user-id {user_id} --text "欢迎加入公司！"

def handle_meeting_reminder(event: Dict):
    """处理会议提醒事件"""
    event_data = event.get("data", {})
    reminder = event_data.get("object", {})
    event_info = reminder.get("event", {})
    
    remind_minutes = reminder.get("remind_minutes", 0)
    if remind_minutes != 30:
        logger.debug(f"非30分钟提醒，跳过: {remind_minutes}分钟前")
        return
    
    meeting_title = event_info.get("summary", "未命名会议")
    start_time = datetime.fromtimestamp(event_info.get("start_time", 0))
    organizer = event_info.get("organizer_name", "")
    attendees = event_info.get("attendees", [])
    meeting_room = event_info.get("location", "")
    
    logger.info(f"=== 会议即将开始（30分钟后） ===")
    logger.info(f"会议主题: {meeting_title}")
    logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"组织者: {organizer}")
    logger.info(f"参会人数: {len(attendees)}")
    if meeting_room:
        logger.info(f"会议室: {meeting_room}")
    
    # 这里可以添加自定义逻辑：发送提醒、准备会议材料等
    # 示例: 给组织者发送提醒确认会议准备情况

def handle_document_change(event: Dict):
    """处理文档变更事件"""
    event_type = event.get("type", "")
    event_data = event.get("data", {})
    doc = event_data.get("object", {})
    
    doc_token = doc.get("doc_token", "")
    doc_name = doc.get("title", "未命名文档")
    modify_time = datetime.now()
    modifier = doc.get("modifier_name", "") if "modifier_name" in doc else doc.get("operator_name", "")
    
    conn = sqlite3.connect("event_records.db")
    cursor = conn.cursor()
    
    # 查询上次修改记录
    cursor.execute("SELECT last_modified FROM document_records WHERE doc_token = ?", (doc_token,))
    last_record = cursor.fetchone()
    
    if last_record:
        last_modified = datetime.fromisoformat(last_record[0])
        time_diff = (modify_time - last_modified).total_seconds()
        if time_diff < 60:  # 1分钟内的多次变更合并为一次
            logger.debug(f"文档短时间内多次变更，跳过: {doc_name}")
            return
    
    logger.info(f"=== 项目文档变更 ===")
    logger.info(f"文档名称: {doc_name}")
    logger.info(f"文档链接: https://bytedance.feishu.cn/doc/{doc_token}")
    logger.info(f"修改人: {modifier}")
    logger.info(f"修改时间: {modify_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 更新记录
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO document_records VALUES (?, ?, ?, ?)",
            (doc_token, doc_name, modify_time, modifier),
        )
        conn.commit()
    finally:
        conn.close()
    
    # 这里可以添加自定义逻辑：通知相关成员、同步备份等

if __name__ == "__main__":
    listener = EventListener()
    
    # 注册需要监听的事件处理器
    listener.register_handler("contact.user.created_v2", handle_new_user)
    listener.register_handler("calendar.event.reminder", handle_meeting_reminder)
    listener.register_handler("doc.document.edit_v1", handle_document_change)
    listener.register_handler("drive.file.update_v1", handle_document_change)
    
    # 启动监听
    listener.start([
        "contact.user.created_v2",
        "calendar.event.reminder",
        "doc.document.edit_v1",
        "drive.file.update_v1"
    ])
