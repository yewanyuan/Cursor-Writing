"""
设置 API
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml

from app.config import get_config, reload_config

router = APIRouter()


class LLMProviderSettings(BaseModel):
    """LLM 提供商设置"""
    api_key: str = ""
    base_url: Optional[str] = None
    model: str = ""
    max_tokens: int = 8000
    temperature: float = 0.7


class AgentSettings(BaseModel):
    """Agent 设置"""
    provider: str = "openai"
    temperature: float = 0.7


class SettingsResponse(BaseModel):
    """设置响应"""
    default_provider: str = "openai"
    providers: Dict[str, LLMProviderSettings] = {}
    agents: Dict[str, AgentSettings] = {}


class SettingsUpdate(BaseModel):
    """设置更新请求"""
    default_provider: Optional[str] = None
    providers: Optional[Dict[str, LLMProviderSettings]] = None
    agents: Optional[Dict[str, AgentSettings]] = None


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """获取当前设置"""
    config = get_config()

    # 获取 LLM 配置
    llm_config = config._config.get("llm", {})
    providers_raw = llm_config.get("providers", {})

    # 转换为响应格式（隐藏 API key 的部分内容）
    providers = {}
    for name, settings in providers_raw.items():
        provider = LLMProviderSettings(**settings) if settings else LLMProviderSettings()
        # 隐藏 API key（只显示后4位）
        if provider.api_key:
            provider.api_key = "*" * 8 + provider.api_key[-4:]
        providers[name] = provider

    # 获取 Agent 配置
    agents_raw = config._config.get("agents", {})
    agents = {}
    for name, settings in agents_raw.items():
        agents[name] = AgentSettings(**settings) if settings else AgentSettings()

    return SettingsResponse(
        default_provider=llm_config.get("default_provider", "openai"),
        providers=providers,
        agents=agents
    )


@router.put("")
async def update_settings(update: SettingsUpdate):
    """更新设置"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"

    # 读取现有配置
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
    else:
        config_data = {}

    # 确保结构存在
    if "llm" not in config_data:
        config_data["llm"] = {}
    if "providers" not in config_data["llm"]:
        config_data["llm"]["providers"] = {}
    if "agents" not in config_data:
        config_data["agents"] = {}

    # 更新默认提供商
    if update.default_provider is not None:
        config_data["llm"]["default_provider"] = update.default_provider

    # 更新提供商配置
    if update.providers is not None:
        for name, provider in update.providers.items():
            if name not in config_data["llm"]["providers"]:
                config_data["llm"]["providers"][name] = {}

            provider_config = config_data["llm"]["providers"][name]

            # 只更新非空值，且不覆盖被隐藏的 API key
            if provider.api_key and not provider.api_key.startswith("*"):
                provider_config["api_key"] = provider.api_key
            if provider.base_url is not None:
                provider_config["base_url"] = provider.base_url
            if provider.model:
                provider_config["model"] = provider.model
            if provider.max_tokens:
                provider_config["max_tokens"] = provider.max_tokens
            if provider.temperature is not None:
                provider_config["temperature"] = provider.temperature

    # 更新 Agent 配置
    if update.agents is not None:
        for name, agent in update.agents.items():
            config_data["agents"][name] = {
                "provider": agent.provider,
                "temperature": agent.temperature
            }

    # 保存配置
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)

    # 重新加载配置
    reload_config()

    # 重建 LLM 客户端，使新 API Key 生效
    from app.llm.client import reset_client
    reset_client()

    return {"success": True, "message": "设置已保存"}


@router.get("/providers")
async def list_available_providers():
    """列出可用的 LLM 提供商（预设模型仅作为建议，用户可自行输入任意模型名）"""
    return {
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI",
                "models": [
                    "gpt-5.2", "gpt-5.1", "gpt-5", "gpt-5-mini",
                    "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
                    "gpt-4o", "gpt-4o-mini",
                    "o3", "o3-mini", "o1", "o1-mini", "o1-pro"
                ]
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "models": [
                    "claude-4.5-sonnet", "claude-4.5-haiku",
                    "claude-4.1-sonnet", "claude-4.1-opus",
                    "claude-sonnet-4-20250514",
                    "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"
                ]
            },
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]
            },
            {"id": "custom", "name": "自定义", "models": []},
        ]
    }


@router.get("/agents")
async def list_agents():
    """列出所有 Agent"""
    return {
        "agents": [
            {"id": "archivist", "name": "资料员", "description": "收集和整理写作素材"},
            {"id": "writer", "name": "撰稿人", "description": "撰写章节内容"},
            {"id": "reviewer", "name": "审稿人", "description": "审核内容质量"},
            {"id": "editor", "name": "编辑", "description": "修订和完善内容"},
        ]
    }


@router.post("/test-connection")
async def test_connection(provider: str, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None):
    """测试 LLM 连接"""
    try:
        from app.llm.providers import (
            OpenAIProvider,
            AnthropicProvider,
            DeepSeekProvider,
            CustomProvider
        )

        # 如果 api_key 为空或是掩码，从现有配置读取真实 key
        if not api_key or api_key.startswith("*"):
            from app.config import get_config
            config = get_config()
            real_key = config.get(f"llm.providers.{provider}.api_key", "")
            if not real_key or real_key.startswith("${"):
                return {"success": False, "message": "请输入有效的 API Key"}
            api_key = real_key

        # 根据提供商类型创建实例
        if provider == "openai":
            llm = OpenAIProvider(
                api_key=api_key,
                model=model or "gpt-4o",
                max_tokens=100,
                temperature=0.7
            )
        elif provider == "anthropic":
            llm = AnthropicProvider(
                api_key=api_key,
                model=model or "claude-3-5-sonnet-20241022",
                max_tokens=100,
                temperature=0.7
            )
        elif provider == "deepseek":
            llm = DeepSeekProvider(
                api_key=api_key,
                model=model or "deepseek-chat",
                max_tokens=100,
                temperature=0.7
            )
        elif provider == "custom":
            if not base_url:
                return {"success": False, "message": "自定义提供商需要设置 Base URL"}
            llm = CustomProvider(
                api_key=api_key,
                base_url=base_url,
                model=model or "gpt-3.5-turbo",
                max_tokens=100,
                temperature=0.7
            )
        else:
            return {"success": False, "message": f"不支持的提供商: {provider}"}

        # 发送测试请求
        result = await llm.chat([{"role": "user", "content": "Hello, reply with 'OK' only."}])
        response_text = result.get("content", "")

        return {
            "success": True,
            "message": "连接成功",
            "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}"
        }
