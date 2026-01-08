"""
Agent 基类
所有智能体的公共逻辑
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.llm import get_client, LLMClient
from app.storage import CardStorage, CanonStorage, DraftStorage

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """智能体基类"""

    def __init__(
        self,
        card_storage: CardStorage,
        canon_storage: CanonStorage,
        draft_storage: DraftStorage,
        llm_client: Optional[LLMClient] = None
    ):
        self.cards = card_storage
        self.canon = canon_storage
        self.drafts = draft_storage
        self.llm = llm_client or get_client()

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """系统提示词"""
        pass

    @abstractmethod
    async def run(self, project_id: str, chapter: str, **kwargs) -> Dict[str, Any]:
        """执行任务"""
        pass

    async def chat(
        self,
        user_prompt: str,
        context: str = "",
        temperature: Optional[float] = None
    ) -> str:
        """调用 LLM"""
        messages = [{"role": "system", "content": self.system_prompt}]

        if context:
            messages.append({"role": "user", "content": f"参考信息:\n{context}"})
            messages.append({"role": "assistant", "content": "好的，我已了解这些信息。"})

        messages.append({"role": "user", "content": user_prompt})

        provider = self.llm.get_provider_for_agent(self.name)
        temp = temperature or self.llm.get_temperature_for_agent(self.name)

        result = await self.llm.chat(messages, provider=provider, temperature=temp)
        return result["content"]

    def parse_xml_tag(self, text: str, tag: str) -> Optional[str]:
        """提取 XML 标签内容"""
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def parse_to_confirm(self, text: str) -> List[str]:
        """提取 [TO_CONFIRM: xxx] 标记"""
        pattern = r'\[TO_CONFIRM:\s*([^\]]+)\]'
        return re.findall(pattern, text)
