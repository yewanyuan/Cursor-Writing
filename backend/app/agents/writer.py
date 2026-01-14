"""
撰稿人 Agent
负责：根据场景简报生成草稿
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
