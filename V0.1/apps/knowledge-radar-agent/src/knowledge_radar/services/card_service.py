"""
Card Service - 卡片服务

生成飞书卡片
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OutputCard:
    """
    输出卡片
    
    抽象表示要发送的卡片内容
    """
    card_type: str
    title: str
    summary: str
    content: str
    actions: List[Dict[str, Any]]
    source_refs: List[Dict[str, Any]]
    priority: str = "normal"


@dataclass
class FeishuCardPayload:
    """
    飞书卡片载荷
    
    抽象表示飞书卡片的结构
    """
    card_type: str
    elements: List[Dict[str, Any]]
    header: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None


class CardService:
    """
    卡片服务
    
    生成 OutputCard 并转为抽象 FeishuCardPayload
    """
    
    def __init__(self):
        pass
    
    def create_knowledge_card(
        self,
        knowledge_items: List[Dict[str, Any]],
        card_type: str = "summary",
    ) -> OutputCard:
        """
        创建知识卡片
        
        Args:
            knowledge_items: 知识条目列表
            card_type: 卡片类型
        
        Returns:
            OutputCard 对象
        """
        title = self._generate_title(card_type, knowledge_items)
        summary = self._generate_summary(knowledge_items)
        content = self._generate_content(knowledge_items)
        actions = self._generate_actions(knowledge_items)
        source_refs = self._extract_source_refs(knowledge_items)
        
        return OutputCard(
            card_type=card_type,
            title=title,
            summary=summary,
            content=content,
            actions=actions,
            source_refs=source_refs,
            priority="high" if len(knowledge_items) > 3 else "normal",
        )
    
    def _generate_title(self, card_type: str, items: List[Dict[str, Any]]) -> str:
        """生成卡片标题"""
        if card_type == "summary":
            return f"知识雷达 - 今日摘要 ({len(items)}条)"
        elif card_type == "weekly":
            return "知识雷达 - 周报"
        elif card_type == "meeting":
            return "知识雷达 - 会前简报"
        elif card_type == "change":
            return "知识雷达 - 文档变更通知"
        elif card_type == "onboarding":
            return "知识雷达 - 新人入门指南"
        
        return "知识雷达"
    
    def _generate_summary(self, items: List[Dict[str, Any]]) -> str:
        """生成摘要"""
        summaries = []
        
        for item in items[:3]:
            item_summary = item.get("summary", "")[:100]
            summaries.append(f"- {item_summary}...")
        
        return "\n".join(summaries)
    
    def _generate_content(self, items: List[Dict[str, Any]]) -> str:
        """生成内容"""
        content = []
        
        for i, item in enumerate(items[:5], 1):
            title = item.get("title", "")
            summary = item.get("summary", "")[:200]
            content.append(f"**{i}. {title}**\n{summary}\n")
        
        return "\n".join(content)
    
    def _generate_actions(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成操作按钮"""
        actions = []
        
        if items:
            actions.append({
                "type": "view_detail",
                "label": "查看详情",
                "url": "#",
            })
        
        actions.append({
            "type": "feedback",
            "label": "反馈",
        })
        
        return actions
    
    def _extract_source_refs(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取来源引用"""
        refs = []
        
        for item in items:
            refs.extend(item.get("source_refs", []))
        
        return refs
    
    def to_feishu_card(self, output_card: OutputCard) -> FeishuCardPayload:
        """
        转换为飞书卡片载荷
        
        Args:
            output_card: OutputCard 对象
        
        Returns:
            FeishuCardPayload 对象
        
        Note:
            具体字段需要参考飞书官方文档：
            https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN
        """
        # TODO_FEISHU_DOC_LOOKUP: 正式接入时必须核对飞书卡片官方文档
        # 当前为抽象实现，实际字段需要查阅官方文档
        
        header = {
            "title": {
                "content": output_card.title,
                "tag": "plain_text",
            },
        }
        
        elements = [
            {
                "tag": "div",
                "text": {
                    "content": output_card.summary,
                    "tag": "lark_md",
                },
            },
        ]
        
        if output_card.content:
            elements.append({
                "tag": "div",
                "text": {
                    "content": output_card.content,
                    "tag": "lark_md",
                },
            })
        
        actions = []
        for action in output_card.actions:
            if action["type"] == "view_detail":
                actions.append({
                    "tag": "button",
                    "text": {"content": action["label"], "tag": "plain_text"},
                    "type": "primary",
                    "url": action.get("url", "#"),
                })
            elif action["type"] == "feedback":
                actions.append({
                    "tag": "button",
                    "text": {"content": action["label"], "tag": "plain_text"},
                    "type": "default",
                })
        
        return FeishuCardPayload(
            card_type=output_card.card_type,
            header=header,
            elements=elements,
            actions=actions,
        )
