"""
Pytest Configuration
"""

import pytest
import sys
from pathlib import Path

# 确保 src 目录在 PYTHONPATH 中
src_path = Path(__file__).parent / "../src"
src_path = src_path.resolve()
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def mock_feishu_client():
    from knowledge_radar.integrations import MockFeishuClient
    return MockFeishuClient()


@pytest.fixture(scope="session")
def mock_llm_client():
    from knowledge_radar.integrations import LLMClient
    return LLMClient()


@pytest.fixture(scope="session")
def mock_embedding_client():
    from knowledge_radar.integrations import EmbeddingClient
    return EmbeddingClient(use_mock=True)


@pytest.fixture
def sample_chat_messages():
    return [
        {"message_id": "m1", "sender_id": "u1", "content": "消息1"},
        {"message_id": "m2", "sender_id": "u2", "content": "消息2"},
    ]
