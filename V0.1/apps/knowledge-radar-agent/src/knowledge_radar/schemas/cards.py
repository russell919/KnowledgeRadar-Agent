"""
Cards Schema - 卡片消息定义

定义输出卡片的抽象结构
注意：FeishuCardPayload 是抽象的 payload，不绑定具体飞书字段
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class CardAction(BaseModel):
    """
    卡片操作按钮
    
    定义卡片中的可点击操作
    """
    action_id: str = Field(description="操作ID")
    action_type: str = Field(
        description="操作类型: button, link, overflow"
    )
    text: str = Field(description="按钮文本")
    value: Optional[Dict[str, Any]] = Field(
        default=None,
        description="操作携带的值"
    )
    url: Optional[str] = Field(
        default=None,
        description="链接URL（仅 link 类型）"
    )
    confirm: Optional[Dict[str, str]] = Field(
        default=None,
        description="操作确认配置"
    )


class CardSection(BaseModel):
    """
    卡片章节
    
    卡片中的一个内容区块
    """
    section_id: str = Field(description="章节ID")
    title: Optional[str] = Field(
        default=None,
        description="章节标题"
    )
    content: str = Field(description="章节内容（支持 Markdown）")
    actions: List[CardAction] = Field(
        default_factory=list,
        description="章节内的操作按钮"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="章节元数据"
    )


class OutputCard(BaseModel):
    """
    输出卡片
    
    Agent 生成的最终推送卡片
    """
    card_id: str = Field(description="卡片ID")
    run_id: str = Field(description="关联的运行ID")
    scene_type: str = Field(description="场景类型")
    
    # 卡片内容
    header: Dict[str, str] = Field(
        description="卡片头部: title, subtitle"
    )
    sections: List[CardSection] = Field(
        default_factory=list,
        description="卡片章节"
    )
    
    # 底部操作
    footer_actions: List[CardAction] = Field(
        default_factory=list,
        description="底部操作按钮"
    )
    
    # 关联的知识和来源
    knowledge_ids: List[str] = Field(
        default_factory=list,
        description="关联的知识ID"
    )
    source_refs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="来源引用"
    )
    
    # 元数据
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )


class FeishuCardPayload(BaseModel):
    """
    飞书卡片 Payload 抽象
    
    这是抽象的卡片 payload 结构
    具体字段适配需参考飞书官方文档:
    https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/card-v1/card/create
    
    TODO_FEISHU_DOC_LOOKUP:
    - 确认具体的卡片元素字段名
    - 确认卡片版本的差异（v1 vs v2）
    - 确认交互回调的格式
    """
    msg_type: str = Field(
        default="interactive",
        description="消息类型"
    )
    card: Dict[str, Any] = Field(
        description="卡片结构"
    )
    
    # 预留字段（具体实现时填充）
    header: Optional[Dict[str, Any]] = Field(
        default=None,
        description="卡片头部的具体结构待确认"
    )
    elements: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="卡片元素列表的具体结构待确认"
    )
    actions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="操作按钮的具体结构待确认"
    )
    
    # 主题配置
    theme: Optional[str] = Field(
        default="blue",
        description="卡片主题色"
    )
    
    # 尺寸配置
    wide_screen_mode: Optional[bool] = Field(
        default=None,
        description="宽屏模式"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "msg_type": "interactive",
                    "card": {
                        "header": {
                            "title": {"tag": "plain_text", "content": "知识推送"},
                            "template": "blue"
                        },
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": "这是一条测试推送"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
