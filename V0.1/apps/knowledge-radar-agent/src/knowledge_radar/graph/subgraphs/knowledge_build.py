"""
Knowledge Build Subgraph - 知识构建子图

负责从各种来源构建结构化知识
"""

from typing import Dict, Any, Callable
from knowledge_radar.graph.agent_graph import KnowledgeRadarState


def build_knowledge_build_subgraph() -> Dict[str, Callable]:
    """
    构建知识构建子图
    
    流程：
    source_type_router → parse_doc_structure / build_chat_episodes / normalize_task / normalize_bitable
    → extract_knowledge_events → link_entities → deduplicate_knowledge
    → manage_validity → write_indexes
    """
    nodes = {}
    
    async def source_type_router(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        路由来源类型
        
        输入: source_type
        输出: next_node
        """
        source_type = state.source_type
        
        routing = {
            "doc": "parse_doc_structure",
            "chat": "build_chat_episodes",
            "task": "normalize_task",
            "bitable": "normalize_bitable",
            "meeting": "parse_meeting_note",
        }
        
        return {"next_node": routing.get(source_type, "extract_knowledge_events")}
    
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
                {
                    "block_id": b.block_id,
                    "block_type": b.block_type,
                    "content": b.content,
                    "section_path": b.section_path,
                    "level": b.level,
                    "order": b.order,
                }
                for b in blocks
            ],
        }
    
    async def build_chat_episodes(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        构建聊天会话片段
        
        输入: raw_content (chat_id, messages)
        输出: parsed_blocks (作为 chat_episodes)
        """
        from knowledge_radar.services import ChatEpisodeService
        from knowledge_radar.integrations import MockFeishuClient
        
        client = MockFeishuClient()
        messages = await client.read_chat_history(state.source_id)
        
        service = ChatEpisodeService()
        episodes = service.reconstruct_episodes(messages, state.source_id)
        
        return {
            "parsed_blocks": [
                {
                    "episode_id": e.episode_id,
                    "messages": e.messages,
                    "participants": e.participants,
                    "start_time": e.start_time.isoformat() if hasattr(e.start_time, 'isoformat') else str(e.start_time),
                    "end_time": e.end_time.isoformat() if hasattr(e.end_time, 'isoformat') else str(e.end_time),
                    "topic": e.topic,
                }
                for e in episodes
            ],
        }
    
    async def normalize_task(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        规范化任务
        
        输入: raw_content (task_id)
        输出: parsed_blocks
        """
        from knowledge_radar.integrations import MockFeishuClient
        
        client = MockFeishuClient()
        task_data = await client.read_task(state.source_id)
        
        return {
            "parsed_blocks": [
                {
                    "task_id": task_data.get("task_id"),
                    "title": task_data.get("title"),
                    "status": task_data.get("status"),
                    "owner": task_data.get("owner"),
                    "deadline": task_data.get("deadline"),
                }
            ],
        }
    
    async def normalize_bitable(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        规范化多维表格
        
        输入: raw_content (table_id)
        输出: parsed_blocks
        """
        from knowledge_radar.integrations import MockFeishuClient
        
        client = MockFeishuClient()
        bitable_data = await client.read_bitable(state.source_id)
        
        return {
            "parsed_blocks": [
                {
                    "table_id": bitable_data.get("table_id"),
                    "records": bitable_data.get("records", []),
                }
            ],
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
        extraction_service = ExtractionService(llm_client)
        
        knowledge_items = []
        
        for block in state.parsed_blocks:
            content = block.get("content", "") or str(block)
            
            if len(content) > 50:
                source_ref = {
                    "source_id": state.source_id,
                    "source_type": state.source_type,
                    "block_id": block.get("block_id", ""),
                }
                
                items = await extraction_service.extract_knowledge(
                    text=content,
                    source_ref=source_ref,
                )
                
                knowledge_items.extend([
                    {
                        "knowledge_type": k.knowledge_type,
                        "title": k.title,
                        "summary": k.summary,
                        "key_points": k.key_points,
                        "source_refs": [k.source_ref],
                        "confidence_score": k.confidence,
                    }
                    for k in items
                ])
        
        return {"extracted_knowledge": knowledge_items}
    
    async def link_entities(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        链接实体
        
        输入: extracted_knowledge
        输出: linked_entities
        """
        from knowledge_radar.services import EntityLinkingService
        
        service = EntityLinkingService()
        
        all_links = []
        for item in state.extracted_knowledge:
            entities = service.extract_entities(item.get("summary", ""))
            all_links.extend(entities)
        
        return {
            "linked_entities": [
                {
                    "source_entity_type": link.source_entity_type,
                    "source_entity_id": link.source_entity_id,
                    "target_entity_type": link.target_entity_type,
                    "target_entity_id": link.target_entity_id,
                    "relation_type": link.relation_type,
                    "weight": link.weight,
                }
                for link in all_links
            ],
        }
    
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
    
    async def manage_validity(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        管理有效性
        
        输入: deduplicated_knowledge
        输出: deduplicated_knowledge (filtered)
        """
        from knowledge_radar.services import ValidityService
        
        service = ValidityService()
        valid_items = service.filter_valid_items(state.deduplicated_knowledge)
        
        return {"deduplicated_knowledge": valid_items}
    
    async def write_indexes(state: KnowledgeRadarState) -> Dict[str, Any]:
        """
        写入索引
        
        输入: deduplicated_knowledge
        输出: status
        """
        # TODO: 实际写入数据库索引
        return {"status": "indexed"}
    
    # 注册节点
    nodes["source_type_router"] = source_type_router
    nodes["parse_doc_structure"] = parse_doc_structure
    nodes["build_chat_episodes"] = build_chat_episodes
    nodes["normalize_task"] = normalize_task
    nodes["normalize_bitable"] = normalize_bitable
    nodes["parse_meeting_note"] = normalize_task  # 复用
    nodes["extract_knowledge_events"] = extract_knowledge_events
    nodes["link_entities"] = link_entities
    nodes["deduplicate_knowledge"] = deduplicate_knowledge
    nodes["manage_validity"] = manage_validity
    nodes["write_indexes"] = write_indexes
    
    return nodes


async def run_knowledge_build_subgraph(state: KnowledgeRadarState) -> KnowledgeRadarState:
    """
    运行知识构建子图
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    nodes = build_knowledge_build_subgraph()
    
    # 按顺序执行
    execution_order = [
        "source_type_router",
        "parse_doc_structure",  # 或其他，根据 source_type_router 结果
        "extract_knowledge_events",
        "link_entities",
        "deduplicate_knowledge",
        "manage_validity",
        "write_indexes",
    ]
    
    for node_name in execution_order:
        if node_name not in nodes:
            continue
        
        try:
            result = await nodes[node_name](state)
            
            if isinstance(result, dict):
                for key, value in result.items():
                    if key != "next_node" and hasattr(state, key):
                        setattr(state, key, value)
            
            # 处理路由
            if "next_node" in result:
                next_node = result["next_node"]
                if next_node in nodes and next_node not in execution_order:
                    next_result = await nodes[next_node](state)
                    if isinstance(next_result, dict):
                        for key, value in next_result.items():
                            if hasattr(state, key):
                                setattr(state, key, value)
        
        except Exception as e:
            state.errors.append({
                "node": node_name,
                "error": str(e),
            })
    
    return state
