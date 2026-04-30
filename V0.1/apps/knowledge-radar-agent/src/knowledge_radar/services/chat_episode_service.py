"""
Chat Episode Service - 聊天会话服务

处理聊天消息的会话重建
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ChatEpisode:
    """
    聊天会话片段
    
    表示一个完整的对话单元
    """
    episode_id: str
    messages: List[Dict[str, Any]]
    participants: List[str]
    start_time: datetime
    end_time: datetime
    topic: Optional[str] = None
    entities: Optional[List[str]] = None


class ChatEpisodeService:
    """
    聊天会话服务
    
    实现会话重建：reply/thread 优先、时间窗口、共同实体、共同参与人
    """
    
    def __init__(self, time_window_minutes: int = 30):
        self.time_window_minutes = time_window_minutes
    
    def reconstruct_episodes(
        self,
        messages: List[Dict[str, Any]],
        chat_id: str,
    ) -> List[ChatEpisode]:
        """
        重建聊天会话
        
        Args:
            messages: 消息列表，按时间排序
            chat_id: 聊天ID
        
        Returns:
            会话片段列表
        """
        if not messages:
            return []
        
        # 按时间排序
        sorted_messages = sorted(
            messages,
            key=lambda x: x.get("created_at", "")
        )
        
        episodes = []
        current_episode = None
        current_participants = set()
        
        for msg in sorted_messages:
            msg_time = self._parse_time(msg.get("created_at"))
            
            if current_episode is None:
                # 开始新会话
                current_episode = {
                    "messages": [msg],
                    "participants": {msg.get("sender_id")},
                    "start_time": msg_time,
                    "end_time": msg_time,
                }
                current_participants.add(msg.get("sender_id"))
            else:
                # 检查时间窗口
                time_diff = (msg_time - current_episode["end_time"]).total_seconds() / 60
                
                if time_diff <= self.time_window_minutes:
                    # 在时间窗口内，加入当前会话
                    current_episode["messages"].append(msg)
                    current_episode["participants"].add(msg.get("sender_id"))
                    current_episode["end_time"] = msg_time
                else:
                    # 超出时间窗口，结束当前会话，开始新会话
                    episodes.append(self._create_episode(chat_id, current_episode))
                    current_episode = {
                        "messages": [msg],
                        "participants": {msg.get("sender_id")},
                        "start_time": msg_time,
                        "end_time": msg_time,
                    }
        
        # 添加最后一个会话
        if current_episode:
            episodes.append(self._create_episode(chat_id, current_episode))
        
        return episodes
    
    def _parse_time(self, time_str: Optional[str]) -> datetime:
        """解析时间字符串"""
        if not time_str:
            return datetime.utcnow()
        
        # 尝试多种格式
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        return datetime.utcnow()
    
    def _create_episode(self, chat_id: str, episode_data: dict) -> ChatEpisode:
        """创建会话片段"""
        return ChatEpisode(
            episode_id=f"{chat_id}_{episode_data['start_time'].strftime('%Y%m%d%H%M%S')}",
            messages=episode_data["messages"],
            participants=list(episode_data["participants"]),
            start_time=episode_data["start_time"],
            end_time=episode_data["end_time"],
        )
    
    def extract_episode_content(self, episode: ChatEpisode) -> str:
        """提取会话内容文本"""
        content = []
        for msg in episode.messages:
            content.append(f"{msg.get('sender_id', 'unknown')}: {msg.get('content', '')}")
        return "\n".join(content)
