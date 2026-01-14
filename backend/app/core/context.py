"""
上下文选择器
根据章节目标筛选最相关的信息
"""

import logging
from typing import List, Dict, Any

from app.storage import CardStorage, CanonStorage, DraftStorage

logger = logging.getLogger(__name__)


class ContextSelector:
    """上下文选择器"""

    def __init__(
        self,
        card_storage: CardStorage,
        canon_storage: CanonStorage,
        draft_storage: DraftStorage
    ):
        self.cards = card_storage
        self.canon = canon_storage
        self.drafts = draft_storage

    async def select_for_writing(
        self,
        project_id: str,
        chapter: str,
        chapter_goal: str,
        characters: List[str] = None
    ) -> Dict[str, Any]:
        """
        为写作选择上下文

        返回与章节目标最相关的信息
        """
        context = {
            "characters": [],
            "world": [],
            "style": None,
            "rules": None,
            "facts": [],
            "summaries": []
        }

        # 1. 角色卡 - 指定角色或全部
        if characters:
            char_names = characters
        else:
            char_names = await self.cards.list_characters(project_id)

        for name in char_names[:10]:
            card = await self.cards.get_character(project_id, name)
            if card:
                context["characters"].append(card)

        # 2. 世界观卡 - 简单关键词匹配
        world_names = await self.cards.list_world_cards(project_id)
        for name in world_names[:10]:
            card = await self.cards.get_world_card(project_id, name)
            if card:
                # 简单相关性：名称或描述包含目标关键词
                if self._is_relevant(card.name + card.description, chapter_goal):
                    context["world"].append(card)

        # 如果没匹配到，至少取前3个
        if not context["world"] and world_names:
            for name in world_names[:3]:
                card = await self.cards.get_world_card(project_id, name)
                if card:
                    context["world"].append(card)

        # 3. 文风和规则
        context["style"] = await self.cards.get_style(project_id)
        context["rules"] = await self.cards.get_rules(project_id)

        # 4. 事实 - 最近的 + 相关的
        all_facts = await self.canon.get_facts(project_id)
        recent_facts = all_facts[-10:]
        relevant_facts = [f for f in all_facts[:-10] if self._is_relevant(f.statement, chapter_goal)]
        context["facts"] = relevant_facts[-5:] + recent_facts

        # 5. 前文摘要
        context["summaries"] = await self.drafts.get_previous_summaries(
            project_id, chapter, limit=5
        )

        return context

    def _is_relevant(self, text: str, goal: str) -> bool:
        """简单的相关性判断"""
        if not goal:
            return True

        text_lower = text.lower()
        # 提取目标中的关键词（简单分词）
        keywords = [w for w in goal.lower().split() if len(w) > 1]

        for kw in keywords:
            if kw in text_lower:
                return True

        return False

    def format_context(self, context: Dict[str, Any]) -> str:
        """将上下文格式化为文本"""
        parts = []

        # 角色
        if context["characters"]:
            parts.append("=== 角色 ===")
            for c in context["characters"]:
                parts.append(f"【{c.name}】{c.identity}")
                if c.personality:
                    parts.append(f"  性格: {', '.join(c.personality[:3])}")
                if c.speech_pattern:
                    parts.append(f"  说话风格: {c.speech_pattern}")

        # 世界观
        if context["world"]:
            parts.append("\n=== 世界观 ===")
            for w in context["world"]:
                parts.append(f"【{w.name}】{w.description[:100]}")

        # 文风
        if context["style"]:
            parts.append("\n=== 文风 ===")
            s = context["style"]
            parts.append(f"叙事距离: {s.narrative_distance}, 节奏: {s.pacing}")
            if s.sentence_style:
                parts.append(f"句式: {s.sentence_style}")

        # 规则
        if context["rules"]:
            r = context["rules"]
            if r.donts:
                parts.append("\n=== 禁止事项 ===")
                for d in r.donts[:5]:
                    parts.append(f"- {d}")

        # 事实
        if context["facts"]:
            parts.append("\n=== 已知事实 ===")
            for f in context["facts"][-10:]:
                parts.append(f"- {f.statement}")

        # 前文摘要
        if context["summaries"]:
            parts.append("\n=== 前文摘要 ===")
            for s in context["summaries"]:
                parts.append(f"【{s.chapter}】{s.summary}")

        return "\n".join(parts)
