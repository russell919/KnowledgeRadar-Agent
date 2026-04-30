"""
Knowledge Build Nodes - 知识构建节点
"""

from typing import Dict, Any
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


async def parse_doc_structure(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    解析文档结构
    
    输入: raw_content (doc_id, content)
    输出: parsed_blocks
    """
    from knowledge_radar.services import DocParserService
    from knowledge_radar.integrations import MockFeishuClient
    
    client = MockFeishuClient()
    doc_data = await client.read_doc(state.source_id)
    
    parser = DocParserService()
    blocks = parser.parse(doc_data.get("content", ""), state.source_id)
    
    return {
        "parsed_blocks": [
            {"block_id": b.block_id, "block_type": b.block_type, "content": b.content, "section_path": b.section_path, "level": b.level, "order": b.order}
            for b in blocks
        ]
    }


async def extract_knowledge_events(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    抽取知识事件
    
    输入: parsed_blocks, source_id
    输出: extracted_knowledge
    """
    from knowledge_radar.services import ExtractionService
    from knowledge_radar.integrations import LLMClient
    
    llm_client = LLMClient()
    service = ExtractionService(llm_client)
    
    knowledge_items = []
    
    for block in state.parsed_blocks:
        content = block.get("content", "") or str(block)
        if len(content) > 50:
            source_ref = {"source_id": state.source_id, "source_type": state.source_type, "block_id": block.get("block_id", "")}
            items = await service.extract_knowledge(text=content, source_ref=source_ref)
            knowledge_items.extend([{"knowledge_type": k.knowledge_type, "title": k.title, "summary": k.summary, "source_refs": [k.source_ref], "confidence_score": k.confidence} for k in items])
    
    return {"extracted_knowledge": knowledge_items}


async def deduplicate_knowledge(state: KnowledgeRadarState) -> Dict[str, Any]:
    """
    去重知识
    
    输入: extracted_knowledge
    输出: deduplicated_knowledge
    """
    from knowledge_radar.services import DedupService
    
    service = DedupService()
    unique_items = service.deduplicate_by_hash(state.extracted_knowledge)
    
    return {"deduplicated_knowledge": unique_items}
