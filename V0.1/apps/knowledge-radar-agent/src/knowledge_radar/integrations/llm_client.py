"""
LLM Client - 大语言模型客户端

封装与 LLM 服务的通信
"""

from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel, ValidationError
import json
import asyncio


class LLMClient:
    """
    LLM 客户端
    
    支持 OpenAI-compatible chat completions API
    提供 generate_text 和 generate_json 方法
    """
    
    def __init__(
        self,
        api_base: str = "https://api.openai.com/v1",
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        max_retries: int = 3,
    ):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            生成的文本
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self._call_api(messages, temperature, max_tokens)
        
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    async def generate_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> BaseModel:
        """
        生成 JSON 并校验
        
        Args:
            prompt: 用户提示
            schema: Pydantic schema
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            校验后的 Pydantic 对象
        
        Raises:
            ValueError: 如果 JSON 解析或校验失败
        """
        system_message = f"""
你必须输出严格符合以下 JSON Schema 的数据：
{schema.model_json_schema()}

输出格式必须是纯 JSON，不要包含任何其他文本。
"""
        
        if system_prompt:
            system_message = f"{system_prompt}\n\n{system_message}"
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
        
        response = await self._call_api(messages, temperature, max_tokens)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        try:
            data = json.loads(content)
            return schema(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"JSON 解析或校验失败: {str(e)}")
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """
        调用 LLM API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            API 响应
        """
        for attempt in range(self.max_retries):
            try:
                # 模拟 API 调用
                # 实际实现时需要使用 httpx 或 requests 调用真实 API
                return self._mock_response(messages)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise e
    
    def _mock_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        模拟 API 响应
        
        Args:
            messages: 消息列表
        
        Returns:
            模拟的 API 响应
        """
        user_content = ""
        for msg in messages:
            if msg["role"] == "user":
                user_content = msg["content"]
                break
        
        # 简单模拟响应
        return {
            "choices": [
                {
                    "message": {
                        "content": f"这是对请求的响应: {user_content[:50]}...",
                    }
                }
            ]
        }
