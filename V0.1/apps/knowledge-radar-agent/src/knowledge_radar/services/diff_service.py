"""
Diff Service - 差分服务

处理文档版本之间的差异比较
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ChangeUnit:
    """
    变更单元
    
    表示文档中的一个具体变更
    """
    change_id: str
    change_type: str  # added, modified, deleted, moved
    section_path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    confidence: float = 1.0


class DiffService:
    """
    差分服务
    
    实现文档版本差分：标题路径对齐、段落diff、表格diff、变更单元
    """
    
    def __init__(self):
        pass
    
    def compare_versions(
        self,
        old_version: Dict[str, Any],
        new_version: Dict[str, Any],
    ) -> List[ChangeUnit]:
        """
        比较两个版本的差异
        
        Args:
            old_version: 旧版本数据
            new_version: 新版本数据
        
        Returns:
            变更单元列表
        """
        old_blocks = self._parse_into_blocks(old_version.get("content", ""))
        new_blocks = self._parse_into_blocks(new_version.get("content", ""))
        
        return self._diff_blocks(old_blocks, new_blocks)
    
    def _parse_into_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        将文档内容解析为块
        
        Args:
            content: 文档内容
        
        Returns:
            块列表
        """
        blocks = []
        lines = content.split("\n")
        
        current_section = []
        block_text = []
        
        for line in lines:
            # 检测标题
            import re
            title_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if title_match:
                if block_text:
                    blocks.append({
                        "section_path": "/".join(current_section),
                        "content": "\n".join(block_text),
                    })
                    block_text = []
                
                level = len(title_match.group(1))
                title_text = title_match.group(2)
                
                while len(current_section) >= level:
                    current_section.pop()
                current_section.append(title_text)
                
                blocks.append({
                    "section_path": "/".join(current_section),
                    "content": title_text,
                    "is_title": True,
                })
            else:
                block_text.append(line)
        
        if block_text:
            blocks.append({
                "section_path": "/".join(current_section),
                "content": "\n".join(block_text),
            })
        
        return blocks
    
    def _diff_blocks(
        self,
        old_blocks: List[Dict[str, Any]],
        new_blocks: List[Dict[str, Any]],
    ) -> List[ChangeUnit]:
        """
        比较块的差异
        
        Args:
            old_blocks: 旧块列表
            new_blocks: 新块列表
        
        Returns:
            变更单元列表
        """
        changes = []
        
        # 构建索引
        old_by_section = {b["section_path"]: b for b in old_blocks}
        new_by_section = {b["section_path"]: b for b in new_blocks}
        
        # 检查删除和修改
        for section, old_block in old_by_section.items():
            if section not in new_by_section:
                changes.append(ChangeUnit(
                    change_id=f"del_{hash(section)}",
                    change_type="deleted",
                    section_path=section,
                    old_content=old_block.get("content"),
                ))
            else:
                new_block = new_by_section[section]
                if old_block.get("content") != new_block.get("content"):
                    changes.append(ChangeUnit(
                        change_id=f"mod_{hash(section)}",
                        change_type="modified",
                        section_path=section,
                        old_content=old_block.get("content"),
                        new_content=new_block.get("content"),
                    ))
        
        # 检查新增
        for section, new_block in new_by_section.items():
            if section not in old_by_section:
                changes.append(ChangeUnit(
                    change_id=f"add_{hash(section)}",
                    change_type="added",
                    section_path=section,
                    new_content=new_block.get("content"),
                ))
        
        return changes
    
    def analyze_change_impact(self, change_unit: ChangeUnit) -> Dict[str, Any]:
        """
        分析变更的影响
        
        Args:
            change_unit: 变更单元
        
        Returns:
            影响分析结果
        """
        impact_level = "low"
        affected_areas = []
        
        content_length = len(change_unit.new_content or change_unit.old_content or "")
        
        if content_length > 500:
            impact_level = "high"
        elif content_length > 100:
            impact_level = "medium"
        
        if change_unit.change_type == "deleted":
            impact_level = "high"
            affected_areas.append("内容删除")
        
        if "决策" in (change_unit.new_content or "") or "决定" in (change_unit.new_content or ""):
            impact_level = "high"
            affected_areas.append("决策变更")
        
        if "风险" in (change_unit.new_content or ""):
            impact_level = "high"
            affected_areas.append("风险变更")
        
        return {
            "change_id": change_unit.change_id,
            "impact_level": impact_level,
            "affected_areas": affected_areas,
            "content_length": content_length,
        }
