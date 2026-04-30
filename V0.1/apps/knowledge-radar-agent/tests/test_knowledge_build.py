"""
Test Knowledge Build - 测试知识构建
"""

import pytest
from knowledge_radar.services import DocParserService
from knowledge_radar.integrations import MockFeishuClient


async def test_doc_parsing():
    """测试文档解析"""
    parser = DocParserService()
    content = """# 测试文档
    这是一个测试文档内容"""
    blocks = parser.parse(content, "test-doc-001")

    assert len(blocks) > 0
    assert any(b.block_type == "title" for b in blocks)
    assert any(b.block_type == "paragraph" for b in blocks)


async def test_chat_episode_reconstruction():
    """测试聊天会话重建"""
    from knowledge_radar.services import ChatEpisodeService

    service = ChatEpisodeService()
    messages = [
        {
            "message_id": "m001",
            "sender_id": "u001",
            "content": "你好",
            "created_at": "2024-01-01 10:00:00",
        },
        {
            "message_id": "m002",
            "sender_id": "u002",
            "content": "你好",
            "created_at": "2024-01-01 10:01:00",
        },
    ]

    episodes = service.reconstruct_episodes(messages, "test-chat-001")

    assert len(episodes) == 1
    assert len(episodes[0].messages) == 2


async def test_knowledge_extraction():
    """测试知识抽取"""
    from knowledge_radar.services import ExtractionService
    from knowledge_radar.integrations import LLMClient

    llm_client = LLMClient()
    extraction_service = ExtractionService(llm_client)

    text = "我们决定采用 FastAPI 作为后端框架"
    source_ref = {"source_id": "test-doc"}

    knowledge_list = await extraction_service.extract_knowledge(text, source_ref)

    assert isinstance(knowledge_list, list)
