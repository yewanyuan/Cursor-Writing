"""
LLM 提供商实现
支持 OpenAI、Anthropic、DeepSeek 及自定义 OpenAI 兼容接口
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """提供商基类"""

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_url = base_url

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """发送聊天请求，返回结果"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI 提供商"""

    @property
    def name(self) -> str:
        return "openai"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        from openai import AsyncOpenAI

        # 支持自定义 base_url（用于代理或中转服务）
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = AsyncOpenAI(**client_kwargs)

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens
        )

        choice = response.choices[0]
        return {
            "content": choice.message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "finish_reason": choice.finish_reason
        }


class AnthropicProvider(BaseProvider):
    """Anthropic (Claude) 提供商"""

    @property
    def name(self) -> str:
        return "anthropic"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        from anthropic import AsyncAnthropic

        # 支持自定义 base_url（用于代理或中转服务）
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = AsyncAnthropic(**client_kwargs)

        # Anthropic 格式：system 单独传，其他作为 messages
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)

        response = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            system=system_msg if system_msg else None,
            messages=chat_messages,
            temperature=temperature or self.temperature
        )

        return {
            "content": response.content[0].text,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            "finish_reason": response.stop_reason
        }


class DeepSeekProvider(BaseProvider):
    """DeepSeek 提供商（OpenAI 兼容接口）"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果没有配置 base_url，使用默认值
        if not self.base_url:
            self.base_url = "https://api.deepseek.com/v1"

    @property
    def name(self) -> str:
        return "deepseek"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens
        )

        choice = response.choices[0]
        return {
            "content": choice.message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "finish_reason": choice.finish_reason
        }


class CustomProvider(BaseProvider):
    """自定义 OpenAI 兼容接口（本地模型、其他云服务等）"""

    @property
    def name(self) -> str:
        return "custom"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens
        )

        choice = response.choices[0]
        usage = response.usage
        return {
            "content": choice.message.content,
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0
            },
            "finish_reason": choice.finish_reason
        }
