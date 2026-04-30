"""
Embedding Client - 嵌入向量客户端

封装与 Embedding 服务的通信
"""

from typing import List
import random


class EmbeddingClient:
    """
    Embedding 客户端
    
    提供文本嵌入功能，支持 mock 模式用于测试
    """
    
    def __init__(self, use_mock: bool = False, model: str = "text-embedding-ada-002"):
        self.use_mock = use_mock
        self.model = model
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        为文本列表生成嵌入向量
        
        Args:
            texts: 文本列表
        
        Returns:
            嵌入向量列表
        """
        if self.use_mock:
            return self._generate_mock_embeddings(len(texts))
        
        return await self._call_embedding_api(texts)
    
    async def embed_text(self, text: str) -> List[float]:
        """
        为单个文本生成嵌入向量
        
        Args:
            text: 文本
        
        Returns:
            嵌入向量
        """
        result = await self.embed_texts([text])
        return result[0]
    
    async def _call_embedding_api(self, texts: List[str]) -> List[List[float]]:
        """
        调用真实的 Embedding API
        
        Args:
            texts: 文本列表
        
        Returns:
            嵌入向量列表
        """
        # TODO: 实际实现时需要调用真实的 Embedding API
        # 例如 OpenAI Embeddings API
        return self._generate_mock_embeddings(len(texts))
    
    def _generate_mock_embeddings(self, count: int) -> List[List[float]]:
        """
        生成模拟嵌入向量
        
        Args:
            count: 向量数量
        
        Returns:
            模拟的嵌入向量列表
        """
        embeddings = []
        
        for _ in range(count):
            # 生成 1536 维的随机向量（模拟 ada-002 的维度）
            embedding = [random.uniform(-1, 1) for _ in range(1536)]
            embeddings.append(embedding)
        
        return embeddings
