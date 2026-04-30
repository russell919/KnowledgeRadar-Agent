"""
Ingestion Service - 摄入服务

处理从飞书等来源的数据摄入
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class IngestionService:
    """
    数据摄入服务
    
    负责从各种来源获取数据并进行预处理
    """
    
    def __init__(self, feishu_client):
        self.feishu_client = feishu_client
    
    async def ingest_document(self, doc_id: str) -> Dict[str, Any]:
        """
        摄入文档
        
        Args:
            doc_id: 文档ID
        
        Returns:
            处理后的文档数据
        """
        raw_doc = await self.feishu_client.read_doc(doc_id)
        
        return {
            "source_id": doc_id,
            "source_type": "doc",
            "title": raw_doc.get("title", ""),
            "content": raw_doc.get("content", ""),
            "metadata": {
                "created_at": raw_doc.get("created_at"),
                "updated_at": raw_doc.get("updated_at"),
                "author": raw_doc.get("author"),
            },
            "created_at": datetime.utcnow(),
        }
    
    async def ingest_chat_history(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        摄入聊天历史
        
        Args:
            chat_id: 聊天ID
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            处理后的消息列表
        """
        messages = await self.feishu_client.read_chat_history(
            chat_id, start_time, end_time
        )
        
        processed_messages = []
        for msg in messages:
            processed_messages.append({
                "source_id": msg.get("message_id"),
                "source_type": "im",
                "sender_id": msg.get("sender_id"),
                "content": msg.get("content", ""),
                "created_at": msg.get("created_at"),
            })
        
        return processed_messages
    
    async def ingest_meeting_note(self, meeting_id: str) -> Dict[str, Any]:
        """
        摄入会议纪要
        
        Args:
            meeting_id: 会议ID
        
        Returns:
            处理后的会议纪要数据
        """
        note = await self.feishu_client.read_meeting_note(meeting_id)
        
        return {
            "source_id": meeting_id,
            "source_type": "calendar",
            "title": note.get("title", ""),
            "content": note.get("summary", ""),
            "participants": note.get("participants", []),
            "action_items": note.get("action_items", []),
            "metadata": {
                "date": note.get("date"),
            },
            "created_at": datetime.utcnow(),
        }
    
    async def ingest_calendar_event(self, event_id: str) -> Dict[str, Any]:
        """
        摄入日历事件
        
        Args:
            event_id: 事件ID
        
        Returns:
            处理后的日历事件数据
        """
        event = await self.feishu_client.read_calendar_event(event_id)
        
        return {
            "source_id": event_id,
            "source_type": "calendar",
            "title": event.get("title", ""),
            "start_time": event.get("start_time"),
            "end_time": event.get("end_time"),
            "participants": event.get("participants", []),
            "location": event.get("location"),
            "created_at": datetime.utcnow(),
        }
    
    async def ingest_task(self, task_id: str) -> Dict[str, Any]:
        """
        摄入任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            处理后的任务数据
        """
        task = await self.feishu_client.read_task(task_id)
        
        return {
            "source_id": task_id,
            "source_type": "task",
            "title": task.get("title", ""),
            "status": task.get("status", ""),
            "owner": task.get("owner"),
            "deadline": task.get("deadline"),
            "priority": task.get("priority", "normal"),
            "created_at": datetime.utcnow(),
        }
    
    async def ingest_bitable(self, table_id: str, view_id: Optional[str] = None) -> Dict[str, Any]:
        """
        摄入多维表格
        
        Args:
            table_id: 表格ID
            view_id: 视图ID
        
        Returns:
            处理后的表格数据
        """
        table = await self.feishu_client.read_bitable(table_id, view_id)
        
        return {
            "source_id": table_id,
            "source_type": "base",
            "view_id": table.get("view_id"),
            "records": table.get("records", []),
            "created_at": datetime.utcnow(),
        }
