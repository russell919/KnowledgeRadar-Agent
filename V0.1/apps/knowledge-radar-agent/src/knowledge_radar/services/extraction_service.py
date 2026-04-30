"""
Extraction Service - 知识提取服务

从文档、聊天等来源中提取结构化知识
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExtractedKnowledge:
    """
    提取的知识条目
    """
    knowledge_type: str  # decision, action_item, risk, update, feedback, faq_candidate, reference
    title: str
    summary: str
    key_points: List[str]
    source_ref: Dict[str, Any]
    confidence: float = 0.5


class ExtractionService:
    """
    知识提取服务
    
    从文本中提取决策、行动项、风险点、更新、反馈、FAQ候选、参考资料等知识
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def extract_knowledge(
        self,
        text: str,
        source_ref: Dict[str, Any],
        knowledge_types: Optional[List[str]] = None,
    ) -> List[ExtractedKnowledge]:
        """
        从文本中提取知识
        
        Args:
            text: 文本内容
            source_ref: 来源引用
            knowledge_types: 要提取的知识类型列表
        
        Returns:
            提取的知识条目列表
        """
        if knowledge_types is None:
            knowledge_types = [
                "decision",
                "action_item", 
                "risk",
                "update",
                "feedback",
                "faq_candidate",
                "reference",
            ]
        
        # 使用 LLM 提取知识
        prompt = f"""
请从以下文本中提取结构化知识：

文本：
{text}

请识别以下类型的知识：
{', '.join(knowledge_types)}

请以 JSON 格式输出，每个知识条目包含：
- knowledge_type: 知识类型
- title: 标题（简短描述）
- summary: 摘要（详细描述）
- key_points: 关键点列表
- confidence: 置信度 (0-1)

输出格式：
{{"knowledge": [...]}}
"""
        
        try:
            result = await self.llm_client.generate_text(prompt)
            
            # 解析结果
            import json
            data = json.loads(result)
            extracted = []
            
            for item in data.get("knowledge", []):
                extracted.append(ExtractedKnowledge(
                    knowledge_type=item.get("knowledge_type", ""),
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    key_points=item.get("key_points", []),
                    source_ref=source_ref,
                    confidence=item.get("confidence", 0.5),
                ))
            
            return extracted
        except Exception as e:
            # 如果 LLM 调用失败，返回空列表
            return []
    
    async def extract_from_document(self, doc_data: Dict[str, Any]) -> List[ExtractedKnowledge]:
        """
        从文档数据中提取知识
        
        Args:
            doc_data: 文档数据
        
        Returns:
            提取的知识条目列表
        """
        source_ref = {
            "source_id": doc_data.get("source_id"),
            "source_type": doc_data.get("source_type"),
            "title": doc_data.get("title"),
            "url": doc_data.get("url", ""),
        }
        
        return await self.extract_knowledge(doc_data.get("content", ""), source_ref)
    
    async def extract_from_chat_episode(self, episode_data: Dict[str, Any]) -> List[ExtractedKnowledge]:
        """
        从聊天会话中提取知识
        
        Args:
            episode_data: 会话数据
        
        Returns:
            提取的知识条目列表
        """
        # 提取会话内容
        content = "\n".join([
            f"{msg.get('sender_id', 'unknown')}: {msg.get('content', '')}"
            for msg in episode_data.get("messages", [])
        ])
        
        source_ref = {
            "source_id": episode_data.get("episode_id"),
            "source_type": "im",
            "participants": episode_data.get("participants", []),
        }
        
        return await self.extract_knowledge(content, source_ref)
