"""
资料员 Agent
负责：生成场景简报、提取事实、生成章节摘要
"""

import logging
from typing import Dict, Any, List, Optional

from app.agents.base import BaseAgent
from app.models.draft import SceneBrief, ChapterSummary
from app.models.canon import Fact, TimelineEvent, CharacterState

logger = logging.getLogger(__name__)


class ArchivistAgent(BaseAgent):
    """资料员"""

    @property
    def name(self) -> str:
        return "archivist"

    @property
    def system_prompt(self) -> str:
        return """你是一个小说资料管理员。

职责：
1. 根据章节目标，整理相关的角色、设定、前情信息，生成场景简报
2. 从已完成的章节中提取事实、时间线事件、角色状态变化
3. 生成章节摘要

要求：
- 只整理与本章目标相关的信息，不要罗列无关内容
- 提取的事实必须是明确发生的，不是推测
- 输出使用指定的格式"""

    async def run(self, project_id: str, chapter: str, **kwargs) -> Dict[str, Any]:
        """生成场景简报"""
        chapter_title = kwargs.get("chapter_title", "")
        chapter_goal = kwargs.get("chapter_goal", "")
        characters = kwargs.get("characters", [])

        # 收集上下文
        context_parts = []

        # 角色卡
        char_names = characters or await self.cards.list_characters(project_id)
        for name in char_names[:10]:
            card = await self.cards.get_character(project_id, name)
            if card:
                context_parts.append(f"【角色】{card.name}: {card.identity}, 性格: {', '.join(card.personality)}")

        # 世界观
        world_names = await self.cards.list_world_cards(project_id)
        for name in world_names[:10]:
            card = await self.cards.get_world_card(project_id, name)
            if card:
                context_parts.append(f"【设定】{card.name}: {card.description}")

        # 文风和规则
        style = await self.cards.get_style(project_id)
        rules = await self.cards.get_rules(project_id)

        # 前文摘要
        summaries = await self.drafts.get_previous_summaries(project_id, chapter, limit=3)
        for s in summaries:
            context_parts.append(f"【{s.chapter}摘要】{s.summary}")

        # 最近事实
        facts = await self.canon.get_facts(project_id)
        for f in facts[-10:]:
            context_parts.append(f"【事实】{f.statement}")

        context = "\n".join(context_parts)

        # 生成场景简报
        prompt = f"""为以下章节生成场景简报：

章节：{chapter}
标题：{chapter_title}
目标：{chapter_goal}
出场角色：{', '.join(characters) if characters else '待定'}

请输出：
<brief>
goal: 本章核心目标（一句话）
characters:
  - name: 角色名
    state: 当前状态
    role_in_chapter: 本章作用
timeline_context: 时间背景说明
world_constraints:
  - 需要遵守的设定约束
style_reminder: 文风提醒
forbidden:
  - 禁止事项
</brief>"""

        response = await self.chat(prompt, context)
        brief_text = self.parse_xml_tag(response, "brief") or response

        # 构建 SceneBrief
        brief = SceneBrief(
            chapter=chapter,
            title=chapter_title,
            goal=chapter_goal,
            characters=[{"name": c, "state": "", "role_in_chapter": ""} for c in characters],
            style_reminder=style.sentence_style if style else "",
            forbidden=rules.donts if rules else []
        )

        await self.drafts.save_brief(project_id, brief)

        return {"success": True, "brief": brief, "raw": brief_text}

    async def extract_facts(self, project_id: str, chapter: str, content: str) -> Dict[str, Any]:
        """从章节内容提取事实"""
        prompt = f"""从以下章节内容中提取关键事实：

{content[:3000]}

请提取：
1. 新出现的事实（明确发生的事情）
2. 时间线事件（有时间节点的事件）
3. 角色状态变化

输出格式：
<facts>
- statement: 事实描述
  confidence: 置信度(0-1)
</facts>
<timeline>
- time: 时间
  event: 事件
  participants: [参与者]
</timeline>
<states>
- character: 角色名
  changes: 变化描述
</states>"""

        response = await self.chat(prompt)

        return {"success": True, "raw": response}

    async def generate_summary(self, project_id: str, chapter: str, content: str) -> ChapterSummary:
        """生成章节摘要"""
        prompt = f"""为以下章节生成摘要：

{content[:4000]}

输出格式：
<summary>
简要概述（100字以内）
</summary>
<events>
- 关键事件1
- 关键事件2
</events>"""

        response = await self.chat(prompt)
        summary_text = self.parse_xml_tag(response, "summary") or "（摘要生成失败）"

        summary = ChapterSummary(
            chapter=chapter,
            summary=summary_text,
            key_events=[]
        )

        await self.drafts.save_summary(project_id, summary)
        return summary
