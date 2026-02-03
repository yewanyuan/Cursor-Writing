"""
编辑 Agent
负责：根据审稿意见和用户反馈修订草稿
"""

import logging
from typing import Dict, Any, Optional

from app.agents.base import BaseAgent
from app.models.draft import Draft

logger = logging.getLogger(__name__)


class EditorAgent(BaseAgent):
    """编辑"""

    @property
    def name(self) -> str:
        return "editor"

    @property
    def system_prompt(self) -> str:
        return """你是一个小说编辑。

职责：根据审稿意见和用户反馈修订草稿。

要求：
1. 保持原文风格和语气
2. 只修改有问题的部分，不要大幅改写
3. 修订后仍需符合角色设定
4. 如果用户反馈与审稿意见冲突，以用户反馈为准

输出修订后的完整正文，放在 <draft> 标签中。"""

    async def run(self, project_id: str, chapter: str, **kwargs) -> Dict[str, Any]:
        """修订草稿"""
        version = kwargs.get("version", None)
        user_feedback = kwargs.get("feedback", "")

        # 获取草稿
        if version:
            draft = await self.drafts.get_draft(project_id, chapter, version)
        else:
            draft = await self.drafts.get_latest_draft(project_id, chapter)

        if not draft:
            return {"success": False, "error": "草稿不存在"}

        # 获取审稿意见
        review = await self.drafts.get_review(project_id, chapter)

        # 构建修订指令
        instructions = []

        if review:
            instructions.append(f"审稿评分：{review.overall_score}")
            instructions.append(f"审稿总评：{review.summary}")
            for issue in review.issues[:5]:
                instructions.append(f"- [{issue.category}] {issue.problem} → {issue.suggestion}")

        if user_feedback:
            instructions.append(f"\n用户反馈：{user_feedback}")

        if not instructions:
            instructions.append("请润色文字，提升可读性")

        # 收集参考信息
        context_parts = []

        # 角色信息
        char_names = await self.cards.list_characters(project_id)
        for name in char_names[:5]:
            card = await self.cards.get_character(project_id, name)
            if card:
                context_parts.append(
                    f"【{card.name}】{card.identity}，性格：{', '.join(card.personality[:3])}，说话风格：{card.speech_pattern}"
                )

        # 世界观设定
        world_names = await self.cards.list_world_cards(project_id)
        for name in world_names[:6]:
            world = await self.cards.get_world_card(project_id, name)
            if world:
                context_parts.append(f"【世界观-{world.category}】{world.name}：{world.description[:100]}")

        # 文风卡
        style = await self.cards.get_style(project_id)
        if style:
            context_parts.append(f"【文风】叙事距离：{style.narrative_distance}，节奏：{style.pacing}")
            if style.sentence_style:
                context_parts.append(f"【句式】{style.sentence_style}")
            if style.vocabulary:
                context_parts.append(f"【推荐词汇】{', '.join(style.vocabulary[:15])}")
            if style.taboo_words:
                context_parts.append(f"【禁用词汇】{', '.join(style.taboo_words[:10])}")

        # 规则卡（完整）
        rules = await self.cards.get_rules(project_id)
        if rules:
            if rules.dos:
                context_parts.append(f"【必须遵守】{', '.join(rules.dos[:5])}")
            if rules.donts:
                context_parts.append(f"【禁止事项】{', '.join(rules.donts[:5])}")

        context = "\n".join(context_parts)

        # 修订
        prompt = f"""请根据以下意见修订草稿：

修订指令：
{chr(10).join(instructions)}

原稿：
{draft.content}

输出修订后的完整正文，放在 <draft> 标签中。"""

        response = await self.chat(prompt, context)

        # 解析结果
        revised_content = self.parse_xml_tag(response, "draft")
        if not revised_content:
            revised_content = response

        # 保存新版本
        new_version = await self.drafts.get_next_version(project_id, chapter)
        new_draft = Draft(
            chapter=chapter,
            version=new_version,
            content=revised_content,
            pending_confirmations=self.parse_to_confirm(revised_content)
        )
        await self.drafts.save_draft(project_id, new_draft)

        return {
            "success": True,
            "draft": new_draft,
            "version": new_version,
            "previous_version": draft.version
        }
