"""
Memory Service - 记忆服务

管理 Agent 的长期和短期记忆
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class MemoryService:
    """
    记忆服务
    
    管理对话历史、上下文和长期知识
    """
    
    def __init__(self):
        self.conversation_history = {}
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            对话消息列表
        """
        return self.conversation_history.get(conversation_id, [])
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        添加消息到对话历史
        
        Args:
            conversation_id: 对话ID
            role: 角色（user, assistant, system）
            content: 消息内容
            metadata: 元数据
        """
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        
        self.conversation_history[conversation_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {},
        })
    
    def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取最近的消息
        
        Args:
            conversation_id: 对话ID
            limit: 数量限制
        
        Returns:
            最近的消息列表
        """
        history = self.conversation_history.get(conversation_id, [])
        return history[-limit:]
    
    def clear_conversation(self, conversation_id: str) -> None:
        """
        清除对话历史
        
        Args:
            conversation_id: 对话ID
        """
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
    
    def get_context_summary(self, conversation_id: str) -> str:
        """
        获取上下文摘要
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            上下文摘要
        """
        messages = self.get_recent_messages(conversation_id, 20)
        
        # 提取关键信息
        topics = []
        for msg in messages:
            content = msg.get("content", "")
            if content:
                topics.append(content[:50])
        
        return "; ".join(topics)
