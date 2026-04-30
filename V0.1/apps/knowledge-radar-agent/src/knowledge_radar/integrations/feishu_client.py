"""
Feishu Client - 飞书客户端

封装与飞书 API/CLI 的通信
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class FeishuClient(ABC):
    """
    飞书客户端接口
    
    正式接入时必须核对：
    - 飞书 CLI 文档: https://open.feishu.cn/document/home/index
    - 权限 scope
    - token mode
    - 工具集参数
    """
    
    @abstractmethod
    async def read_doc(self, doc_id: str) -> Dict[str, Any]:
        """读取文档内容"""
        pass
    
    @abstractmethod
    async def read_chat_history(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """读取聊天历史"""
        pass
    
    @abstractmethod
    async def read_meeting_note(self, meeting_id: str) -> Dict[str, Any]:
        """读取会议纪要"""
        pass
    
    @abstractmethod
    async def read_calendar_event(self, event_id: str) -> Dict[str, Any]:
        """读取日历事件"""
        pass
    
    @abstractmethod
    async def read_task(self, task_id: str) -> Dict[str, Any]:
        """读取任务"""
        pass
    
    @abstractmethod
    async def read_bitable(
        self,
        table_id: str,
        view_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """读取多维表格"""
        pass
    
    @abstractmethod
    async def send_card(self, card_payload: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        """发送卡片消息"""
        pass


class MockFeishuClient(FeishuClient):
    """
    模拟飞书客户端
    
    用于 Demo 和测试场景
    """
    
    def __init__(self):
        self.mock_data = {
            "docs": {
                "doc_1": {
                    "doc_id": "doc_1",
                    "title": "项目计划文档",
                    "content": "# 项目计划\n\n## 1. 目标\n完成知识雷达项目开发\n\n## 2. 时间安排\n- 第一阶段：需求分析\n- 第二阶段：架构设计\n- 第三阶段：开发实现\n",
                    "created_at": "2024-01-01T09:00:00Z",
                    "updated_at": "2024-01-15T14:30:00Z",
                    "author": "user_1",
                }
            },
            "chats": {
                "chat_1": [
                    {
                        "message_id": "msg_1",
                        "sender_id": "user_1",
                        "content": "会议时间定在下周三下午3点",
                        "created_at": "2024-01-10T10:00:00Z",
                    },
                    {
                        "message_id": "msg_2",
                        "sender_id": "user_2",
                        "content": "好的，收到",
                        "created_at": "2024-01-10T10:05:00Z",
                    },
                ]
            },
            "meetings": {
                "meeting_1": {
                    "meeting_id": "meeting_1",
                    "title": "项目周会",
                    "summary": "讨论了项目进度和下周计划",
                    "participants": ["user_1", "user_2", "user_3"],
                    "action_items": ["完成技术方案设计", "准备演示材料"],
                    "date": "2024-01-10",
                }
            },
            "events": {
                "event_1": {
                    "event_id": "event_1",
                    "title": "技术分享",
                    "start_time": "2024-01-15T14:00:00Z",
                    "end_time": "2024-01-15T15:00:00Z",
                    "participants": ["user_1", "user_2"],
                    "location": "会议室A",
                }
            },
            "tasks": {
                "task_1": {
                    "task_id": "task_1",
                    "title": "完成文档编写",
                    "status": "pending",
                    "owner": "user_1",
                    "deadline": "2024-01-20",
                    "priority": "high",
                }
            },
            "bitables": {
                "table_1": {
                    "table_id": "table_1",
                    "view_id": "view_1",
                    "records": [
                        {"fields": {"name": "任务A", "status": "完成", "owner": "user_1"}},
                        {"fields": {"name": "任务B", "status": "进行中", "owner": "user_2"}},
                    ],
                }
            },
        }
    
    async def read_doc(self, doc_id: str) -> Dict[str, Any]:
        return self.mock_data["docs"].get(doc_id, {"doc_id": doc_id, "title": "", "content": ""})
    
    async def read_chat_history(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        return self.mock_data["chats"].get(chat_id, [])
    
    async def read_meeting_note(self, meeting_id: str) -> Dict[str, Any]:
        return self.mock_data["meetings"].get(meeting_id, {})
    
    async def read_calendar_event(self, event_id: str) -> Dict[str, Any]:
        return self.mock_data["events"].get(event_id, {})
    
    async def read_task(self, task_id: str) -> Dict[str, Any]:
        return self.mock_data["tasks"].get(task_id, {})
    
    async def read_bitable(
        self,
        table_id: str,
        view_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.mock_data["bitables"].get(table_id, {})
    
    async def send_card(self, card_payload: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        return {"success": True, "message": "卡片发送成功（模拟）"}


class OpenClawFeishuClient(FeishuClient):
    """
    通过 OpenClaw 调用飞书工具的客户端
    
    使用 OpenClaw 已注册的飞书工具进行操作
    """
    
    def __init__(self, openclaw_client):
        self.openclaw_client = openclaw_client
    
    async def read_doc(self, doc_id: str) -> Dict[str, Any]:
        return await self.openclaw_client.send_tool_request(
            tool_name="feishu.read_doc",
            tool_params={"doc_id": doc_id},
            user_id="",
            conversation_id="",
        )
    
    async def read_chat_history(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        params = {"chat_id": chat_id}
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()
        
        result = await self.openclaw_client.send_tool_request(
            tool_name="feishu.read_chat_history",
            tool_params=params,
            user_id="",
            conversation_id="",
        )
        
        return result.get("data", [])
    
    async def read_meeting_note(self, meeting_id: str) -> Dict[str, Any]:
        return await self.openclaw_client.send_tool_request(
            tool_name="feishu.read_meeting_note",
            tool_params={"meeting_id": meeting_id},
            user_id="",
            conversation_id="",
        )
    
    async def read_calendar_event(self, event_id: str) -> Dict[str, Any]:
        return await self.openclaw_client.send_tool_request(
            tool_name="feishu.read_calendar_event",
            tool_params={"event_id": event_id},
            user_id="",
            conversation_id="",
        )
    
    async def read_task(self, task_id: str) -> Dict[str, Any]:
        return await self.openclaw_client.send_tool_request(
            tool_name="feishu.read_task",
            tool_params={"task_id": task_id},
            user_id="",
            conversation_id="",
        )
    
    async def read_bitable(
        self,
        table_id: str,
        view_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {"table_id": table_id}
        if view_id:
            params["view_id"] = view_id
        
        return await self.openclaw_client.send_tool_request(
            tool_name="feishu.read_bitable",
            tool_params=params,
            user_id="",
            conversation_id="",
        )
    
    async def send_card(self, card_payload: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        return await self.openclaw_client.send_tool_request(
            tool_name="feishu.send_card",
            tool_params={"card_payload": card_payload, "chat_id": chat_id},
            user_id="",
            conversation_id="",
        )


class FeishuCLIClient(FeishuClient):
    """
    飞书 CLI 客户端（占位实现）
    
    所有未确认命令抛出 NotImplementedError 并带 TODO_FEISHU_DOC_LOOKUP
    """
    
    async def read_doc(self, doc_id: str) -> Dict[str, Any]:
        raise NotImplementedError("TODO_FEISHU_DOC_LOOKUP: 需要确认飞书 CLI 命令")
    
    async def read_chat_history(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("TODO_FEISHU_DOC_LOOKUP: 需要确认飞书 CLI 命令")
    
    async def read_meeting_note(self, meeting_id: str) -> Dict[str, Any]:
        raise NotImplementedError("TODO_FEISHU_DOC_LOOKUP: 需要确认飞书 CLI 命令")
    
    async def read_calendar_event(self, event_id: str) -> Dict[str, Any]:
        raise NotImplementedError("TODO_FEISHU_DOC_LOOKUP: 需要确认飞书 CLI 命令")
    
    async def read_task(self, task_id: str) -> Dict[str, Any]:
        raise NotImplementedError("TODO_FEISHU_DOC_LOOKUP: 需要确认飞书 CLI 命令")
    
    async def read_bitable(
        self,
        table_id: str,
        view_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("TODO_FEISHU_DOC_LOOKUP: 需要确认飞书 CLI 命令")
    
    async def send_card(self, card_payload: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        raise NotImplementedError("TODO_FEISHU_DOC_LOOKUP: 需要确认飞书 CLI 命令")
