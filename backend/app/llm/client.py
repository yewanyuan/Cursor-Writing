"""
LLM 客户端
统一接口，支持重试和多提供商切换
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

from app.config import get_config
from app.llm.providers import (
    BaseProvider,
    OpenAIProvider,
    AnthropicProvider,
    DeepSeekProvider,
    CustomProvider
)
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端"""

    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.config = get_config()
        self._init_providers()

        # 统计
        self.total_requests = 0
        self.total_tokens = 0

    def _init_providers(self):
        """初始化已配置的提供商"""
        llm_config = self.config.get("llm.providers", {})

        # OpenAI
        if "openai" in llm_config:
            cfg = llm_config["openai"]
            if self._has_valid_key(cfg.get("api_key")):
                self.providers["openai"] = OpenAIProvider(
                    api_key=cfg["api_key"],
                    model=cfg.get("model", "gpt-5"),
                    max_tokens=cfg.get("max_tokens", 4000),
                    temperature=cfg.get("temperature", 0.7)
                )

        # Anthropic
        if "anthropic" in llm_config:
            cfg = llm_config["anthropic"]
            if self._has_valid_key(cfg.get("api_key")):
                self.providers["anthropic"] = AnthropicProvider(
                    api_key=cfg["api_key"],
                    model=cfg.get("model", "claude-4-5-sonnet-20241022"),
                    max_tokens=cfg.get("max_tokens", 4000),
                    temperature=cfg.get("temperature", 0.7)
                )

        # DeepSeek
        if "deepseek" in llm_config:
            cfg = llm_config["deepseek"]
            if self._has_valid_key(cfg.get("api_key")):
                self.providers["deepseek"] = DeepSeekProvider(
                    api_key=cfg["api_key"],
                    model=cfg.get("model", "deepseek-chat"),
                    max_tokens=cfg.get("max_tokens", 4000),
                    temperature=cfg.get("temperature", 0.7)
                )

        # Custom
        if "custom" in llm_config:
            cfg = llm_config["custom"]
            if cfg.get("base_url"):
                self.providers["custom"] = CustomProvider(
                    api_key=cfg.get("api_key", ""),
                    base_url=cfg["base_url"],
                    model=cfg.get("model", ""),
                    max_tokens=cfg.get("max_tokens", 4000),
                    temperature=cfg.get("temperature", 0.7)
                )

        logger.info(f"已初始化 LLM 提供商: {list(self.providers.keys())}")

    def _has_valid_key(self, key: Optional[str]) -> bool:
        """检查 API Key 是否有效（非占位符）"""
        if not key:
            return False
        placeholders = ["sk-your-", "your-", "xxx", "placeholder"]
        return not any(key.lower().startswith(p) for p in placeholders)

    @property
    def default_provider(self) -> str:
        """默认提供商"""
        return self.config.get("llm.default_provider", "openai")

    @property
    def available_providers(self) -> List[str]:
        """可用的提供商列表"""
        return list(self.providers.keys())

    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry: int = 3
    ) -> Dict[str, Any]:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            provider: 提供商名称，None 则用默认
            temperature: 温度参数
            max_tokens: 最大 token 数
            retry: 重试次数

        Returns:
            {"content": "...", "usage": {...}, "provider": "..."}
        """
        provider_name = provider or self.default_provider

        if provider_name not in self.providers:
            available = self.available_providers
            if not available:
                raise LLMError("没有可用的 LLM 提供商，请检查配置")
            # 回退到第一个可用的
            provider_name = available[0]
            logger.warning(f"提供商 {provider} 不可用，回退到 {provider_name}")

        llm = self.providers[provider_name]

        # 带重试的请求
        last_error = None
        for attempt in range(retry):
            try:
                result = await llm.chat(messages, temperature, max_tokens)
                result["provider"] = provider_name

                # 更新统计
                self.total_requests += 1
                self.total_tokens += result.get("usage", {}).get("total_tokens", 0)

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"LLM 请求失败 (尝试 {attempt + 1}/{retry}): {e}")
                if attempt < retry - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避

        raise LLMError(f"LLM 请求失败: {last_error}", provider_name)

    def get_provider_for_agent(self, agent_name: str) -> str:
        """获取 Agent 配置的提供商"""
        agent_cfg = self.config.get(f"agents.{agent_name}", {})
        provider = agent_cfg.get("provider", self.default_provider)

        # 如果配置的提供商不可用，回退
        if provider not in self.providers and self.providers:
            return list(self.providers.keys())[0]
        return provider

    def get_temperature_for_agent(self, agent_name: str) -> float:
        """获取 Agent 配置的温度"""
        agent_cfg = self.config.get(f"agents.{agent_name}", {})
        return agent_cfg.get("temperature", 0.7)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "available_providers": self.available_providers
        }


# 全局实例
_client: Optional[LLMClient] = None


def get_client() -> LLMClient:
    """获取全局 LLM 客户端"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def reset_client():
    """重置客户端（配置变更后调用）"""
    global _client
    _client = None
