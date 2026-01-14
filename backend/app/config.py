"""
配置管理 (Configuration Management)
统一管理所有配置项
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class LLMProviderConfig(BaseModel):
    """LLM 提供商配置"""
    api_key: str = ""
    base_url: Optional[str] = None
    model: str = ""
    max_tokens: int = 8000
    temperature: float = 0.7


class AgentConfig(BaseModel):
    """单个 Agent 配置"""
    provider: str = "openai"
    temperature: float = 0.7


class Settings(BaseSettings):
    """应用设置（从环境变量加载）"""

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # 数据目录
    data_dir: str = "../data"

    # API Keys（从环境变量加载）
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    custom_api_key: str = ""
    custom_base_url: str = ""

    # 模型选择
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    deepseek_model: str = "deepseek-chat"
    custom_model: str = ""

    # 全局 LLM 覆盖
    default_provider: str = "openai"

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class AppConfig:
    """
    应用配置管理器
    合并 config.yaml 和环境变量
    """

    def __init__(self, config_path: Optional[str] = None):
        self.settings = Settings()
        self._config: Dict[str, Any] = {}

        # 加载 YAML 配置
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        self._load_yaml_config(config_path)
        self._merge_env_settings()

    def _load_yaml_config(self, config_path: Path) -> None:
        """加载 YAML 配置文件"""
        if Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}

    def _merge_env_settings(self) -> None:
        """将环境变量合并到配置中"""
        # LLM 提供商配置
        if "llm" not in self._config:
            self._config["llm"] = {"providers": {}}

        providers = self._config["llm"].setdefault("providers", {})

        # OpenAI
        if self.settings.openai_api_key:
            providers.setdefault("openai", {})
            providers["openai"]["api_key"] = self.settings.openai_api_key
            providers["openai"]["model"] = self.settings.openai_model

        # Anthropic
        if self.settings.anthropic_api_key:
            providers.setdefault("anthropic", {})
            providers["anthropic"]["api_key"] = self.settings.anthropic_api_key
            providers["anthropic"]["model"] = self.settings.anthropic_model

        # DeepSeek
        if self.settings.deepseek_api_key:
            providers.setdefault("deepseek", {})
            providers["deepseek"]["api_key"] = self.settings.deepseek_api_key
            providers["deepseek"]["model"] = self.settings.deepseek_model

        # Custom
        if self.settings.custom_api_key or self.settings.custom_base_url:
            providers.setdefault("custom", {})
            providers["custom"]["api_key"] = self.settings.custom_api_key
            providers["custom"]["base_url"] = self.settings.custom_base_url
            providers["custom"]["model"] = self.settings.custom_model

        # 默认提供商
        self._config["llm"]["default_provider"] = self.settings.default_provider

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点号分隔的路径）"""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def get_provider_config(self, provider: str) -> LLMProviderConfig:
        """获取 LLM 提供商配置"""
        providers = self._config.get("llm", {}).get("providers", {})
        provider_config = providers.get(provider, {})
        return LLMProviderConfig(**provider_config)

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """获取 Agent 配置"""
        agents = self._config.get("agents", {})
        agent_config = agents.get(agent_name, {})
        return AgentConfig(**agent_config)

    @property
    def data_dir(self) -> Path:
        """获取数据目录路径"""
        return Path(self.settings.data_dir).resolve()


# 全局配置实例
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """重新加载配置"""
    global _config
    _config = AppConfig()
    return _config
