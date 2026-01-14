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

    return {"success": True, "message": "设置已保存"}


@router.get("/providers")
async def list_available_providers():
    """列出可用的 LLM 提供商"""
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI", "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]},
            {"id": "deepseek", "name": "DeepSeek", "models": ["deepseek-chat", "deepseek-coder"]},
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
        from app.llm import LLMClient
        from app.config import LLMProviderConfig

        config = LLMProviderConfig(
            api_key=api_key,
            base_url=base_url,
            model=model or "gpt-4o",
            max_tokens=100,
            temperature=0.7
        )

        client = LLMClient(provider, config)
        response = await client.generate([{"role": "user", "content": "Hello"}])

        return {
            "success": True,
            "message": "连接成功",
            "response_preview": response[:100] + "..." if len(response) > 100 else response
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}"
        }
