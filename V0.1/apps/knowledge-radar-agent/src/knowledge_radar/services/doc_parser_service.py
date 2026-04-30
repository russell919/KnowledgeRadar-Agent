"""
Doc Parser Service - 文档解析服务

处理文档结构解析和切分
"""

from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class DocumentBlock:
    """
    文档块
    
    表示文档中的一个结构化单元
    """
    block_id: str
    block_type: Literal["title", "paragraph", "list", "table", "code", "quote"]
    content: str
    section_path: str
    level: int = 0
    order: int = 0


class DocParserService:
    """
    文档解析服务
    
    实现结构优先切分：标题路径、段落、列表、表格
    """
    
    def __init__(self, max_block_size: int = 2000):
        self.max_block_size = max_block_size
    
    def parse(self, content: str, doc_id: str) -> List[DocumentBlock]:
        """
        解析文档内容
        
        Args:
            content: 文档内容（支持 Markdown 格式）
            doc_id: 文档ID
        
        Returns:
            文档块列表
        """
        blocks = []
        lines = content.split("\n")
        
        current_section = []
        current_block = []
        block_type: str = "paragraph"
        order = 0
        
        for line in lines:
            # 检测标题
            title_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if title_match:
                # 保存当前块
                if current_block:
                    blocks.append(self._create_block(
                        doc_id, block_type, "\n".join(current_block), current_section, order
                    ))
                    order += 1
                
                # 更新当前章节
                level = len(title_match.group(1))
                title_text = title_match.group(2)
                
                # 保持正确的标题层级
                while len(current_section) >= level:
                    current_section.pop()
                current_section.append(title_text)
                
                # 创建标题块
                blocks.append(self._create_block(
                    doc_id, "title", title_text, current_section.copy(), order, level
                ))
                order += 1
                current_block = []
                block_type = "paragraph"
                continue
            
            # 检测列表
            if line.startswith(("- ", "* ", "+ ", "1. ", "• ")):
                if block_type != "list":
                    if current_block:
                        blocks.append(self._create_block(
                            doc_id, block_type, "\n".join(current_block), current_section, order
                        ))
                        order += 1
                    current_block = []
                    block_type = "list"
                current_block.append(line)
                continue
            
            # 检测代码块
            if line.startswith("```"):
                if current_block:
                    blocks.append(self._create_block(
                        doc_id, block_type, "\n".join(current_block), current_section, order
                    ))
                    order += 1
                current_block = [line]
                block_type = "code"
                continue
            
            # 检测引用
            if line.startswith("> "):
                if block_type != "quote":
                    if current_block:
                        blocks.append(self._create_block(
                            doc_id, block_type, "\n".join(current_block), current_section, order
                        ))
                        order += 1
                    current_block = []
                    block_type = "quote"
                current_block.append(line[2:])  # 移除 "> "
                continue
            
            # 检测表格（简单检测）
            if "|" in line and re.match(r"^\|.*\|$", line):
                if block_type != "table":
                    if current_block:
                        blocks.append(self._create_block(
                            doc_id, block_type, "\n".join(current_block), current_section, order
                        ))
                        order += 1
                    current_block = []
                    block_type = "table"
                current_block.append(line)
                continue
            
            # 普通段落
            if line.strip():
                if block_type == "code" and line.startswith("```"):
                    # 代码块结束
                    current_block.append(line)
                    blocks.append(self._create_block(
                        doc_id, block_type, "\n".join(current_block), current_section, order
                    ))
                    order += 1
                    current_block = []
                    block_type = "paragraph"
                else:
                    if block_type == "paragraph" and current_block and len("\n".join(current_block)) > self.max_block_size:
                        # 过长段落切分
                        blocks.append(self._create_block(
                            doc_id, block_type, "\n".join(current_block), current_section, order
                        ))
                        order += 1
                        current_block = []
                    current_block.append(line)
        
        # 处理最后一个块
        if current_block:
            blocks.append(self._create_block(
                doc_id, block_type, "\n".join(current_block), current_section, order
            ))
        
        return blocks
    
    def _create_block(
        self,
        doc_id: str,
        block_type: str,
        content: str,
        section: List[str],
        order: int,
        level: int = 0,
    ) -> DocumentBlock:
        """创建文档块"""
        return DocumentBlock(
            block_id=f"{doc_id}_{order}",
            block_type=block_type,
            content=content.strip(),
            section_path="/".join(section),
            level=level,
            order=order,
        )
