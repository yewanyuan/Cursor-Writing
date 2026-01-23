"""
撰稿人 Agent
负责：根据场景简报生成草稿，支持续写和插入
"""

import logging
from typing import Dict, Any, Optional

from app.agents.base import BaseAgent
from app.models.draft import Draft

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """撰稿人"""

    @property
    def name(self) -> str:
        return "writer"

    @property
    def system_prompt(self) -> str:
        return """你是一个小说撰稿人。

职责：根据场景简报撰写章节草稿。

要求：
1. 严格遵循文风指南
2. 不要发明新设定，不确定的地方用 [TO_CONFIRM: 说明] 标记
3. 保持角色性格一致
4. 章节目标优先，不要为了堆设定而偏离主线

输出格式：
<plan>
1. 场景节拍1
2. 场景节拍2
...
</plan>
<draft>
正文内容
</draft>"""

    async def run(self, project_id: str, chapter: str, **kwargs) -> Dict[str, Any]:
        """生成草稿"""
        chapter_goal = kwargs.get("chapter_goal", "")
        target_words = kwargs.get("target_words", 2000)

        # 获取场景简报
        brief = await self.drafts.get_brief(project_id, chapter)
        if not brief:
            return {"success": False, "error": "场景简报不存在"}

        # 收集上下文
        context_parts = []

        # 场景简报
        context_parts.append(f"【章节目标】{brief.goal}")
        context_parts.append(f"【文风提醒】{brief.style_reminder}")
        if brief.forbidden:
            context_parts.append(f"【禁止事项】{', '.join(brief.forbidden)}")

        # 角色信息
        for char in brief.characters:
            name = char.get("name", "")
            if name:
                card = await self.cards.get_character(project_id, name)
                if card:
                    context_parts.append(
                        f"【{card.name}】{card.identity}，性格：{', '.join(card.personality[:3])}，"
                        f"说话风格：{card.speech_pattern}"
                    )

        # 文风卡
        style = await self.cards.get_style(project_id)
        if style and style.example_passages:
            context_parts.append(f"【范文参考】{style.example_passages[0][:200]}")

        # 前文摘要
        summaries = await self.drafts.get_previous_summaries(project_id, chapter, limit=3)
        for s in summaries:
            context_parts.append(f"【{s.chapter}】{s.summary}")

        context = "\n".join(context_parts)

        # 生成草稿
        prompt = f"""请撰写章节草稿。

章节：{chapter}
目标：{chapter_goal or brief.goal}
目标字数：约 {target_words} 字

要求：
- 先列出 3-5 个场景节拍（放在 <plan> 中）
- 然后写正文（放在 <draft> 中）
- 不确定的细节用 [TO_CONFIRM: 说明] 标记"""

        response = await self.chat(prompt, context)

        # 解析结果
        draft_content = self.parse_xml_tag(response, "draft")
        if not draft_content:
            # 没有标签就用整个响应
            draft_content = response

        # 提取待确认项
        confirmations = self.parse_to_confirm(draft_content)

        # 获取下一个版本号并保存
        version = await self.drafts.get_next_version(project_id, chapter)
        draft = Draft(
            chapter=chapter,
            version=version,
            content=draft_content,
            pending_confirmations=confirmations
        )
        await self.drafts.save_draft(project_id, draft)

        return {
            "success": True,
            "draft": draft,
            "version": version,
            "confirmations": confirmations
        }

    async def continue_writing(
        self,
        project_id: str,
        chapter: str,
        existing_content: str,
        instruction: str,
        target_words: int = 500,
        insert_position: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        续写或插入内容

        Args:
            project_id: 项目 ID
            chapter: 章节
            existing_content: 现有内容
            instruction: 续写指令（描述要写什么）
            target_words: 目标字数
            insert_position: 插入位置（字符索引），None 表示在末尾续写

        Returns:
            包含新内容的结果
        """
        # 收集上下文
        context_parts = []

        # 角色信息
        char_names = await self.cards.list_characters(project_id)
        for name in char_names[:5]:
            card = await self.cards.get_character(project_id, name)
            if card:
                context_parts.append(
                    f"【{card.name}】{card.identity}，性格：{', '.join(card.personality[:3])}"
                )

        # 文风卡
        style = await self.cards.get_style(project_id)
        if style:
            context_parts.append(f"【文风】叙事距离：{style.narrative_distance}，节奏：{style.pacing}")
            if style.sentence_style:
                context_parts.append(f"【句式】{style.sentence_style}")

        # 规则
        rules = await self.cards.get_rules(project_id)
        if rules and rules.donts:
            context_parts.append(f"【禁止事项】{', '.join(rules.donts[:3])}")

        context = "\n".join(context_parts)

        # 根据插入位置构建 prompt
        if insert_position is None:
            # 末尾续写
            prompt = f"""请续写以下章节内容。

【已有内容】（最后 1500 字）
{existing_content[-1500:]}

【续写要求】
{instruction}

【目标字数】约 {target_words} 字

要求：
1. 保持文风一致
2. 自然衔接上文
3. 只输出续写的新内容，不要重复已有内容
4. 不确定的细节用 [TO_CONFIRM: 说明] 标记

请直接输出续写内容："""
        else:
            # 中间插入
            before = existing_content[:insert_position]
            after = existing_content[insert_position:]

            # 取插入点前后各 500 字作为上下文
            before_context = before[-500:] if len(before) > 500 else before
            after_context = after[:500] if len(after) > 500 else after

            prompt = f"""请在指定位置插入新内容。

【插入点之前的内容】
{before_context}

【插入点之后的内容】
{after_context}

【插入要求】
{instruction}

【目标字数】约 {target_words} 字

要求：
1. 保持文风一致
2. 自然衔接前后文
3. 只输出要插入的新内容
4. 不确定的细节用 [TO_CONFIRM: 说明] 标记

请直接输出要插入的内容："""

        response = await self.chat(prompt, context)

        # 清理响应（移除可能的标签）
        new_content = response.strip()
        if new_content.startswith("<draft>"):
            new_content = self.parse_xml_tag(response, "draft") or new_content

        # 提取待确认项
        confirmations = self.parse_to_confirm(new_content)

        # 合并内容
        if insert_position is None:
            # 末尾续写
            merged_content = existing_content.rstrip() + "\n\n" + new_content
        else:
            # 中间插入
            merged_content = (
                existing_content[:insert_position] +
                "\n\n" + new_content + "\n\n" +
                existing_content[insert_position:].lstrip()
            )

        # 保存新版本
        version = await self.drafts.get_next_version(project_id, chapter)
        draft = Draft(
            chapter=chapter,
            version=version,
            content=merged_content,
            pending_confirmations=confirmations,
            notes=f"续写：{instruction[:50]}"
        )
        await self.drafts.save_draft(project_id, draft)

        return {
            "success": True,
            "draft": draft,
            "new_content": new_content,
            "version": version,
            "confirmations": confirmations,
            "insert_position": insert_position
        }
