"""
审稿人 Agent
负责：审核草稿质量，检查一致性问题
"""

import logging
from typing import Dict, Any, List

from app.agents.base import BaseAgent
from app.models.draft import Review, ReviewIssue

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    """审稿人"""

    @property
    def name(self) -> str:
        return "reviewer"

    @property
    def system_prompt(self) -> str:
        return """你是一个小说审稿人。

职责：审核草稿，找出问题并给出修改建议。

审核维度：
1. consistency - 前后一致性（与已有设定、前文是否矛盾）
2. character - 角色塑造（言行是否符合人设）
3. plot - 情节逻辑（是否合理、是否推进了目标）
4. style - 文风（是否符合要求）

问题严重程度：
- critical: 严重问题，必须修改
- major: 较大问题，建议修改
- minor: 小问题，可选修改

输出格式：
<issues>
- category: 类别
  severity: 严重程度
  problem: 问题描述
  suggestion: 修改建议
</issues>
<score>0.0-1.0</score>
<summary>总体评价</summary>"""

    async def run(self, project_id: str, chapter: str, **kwargs) -> Dict[str, Any]:
        """审核草稿"""
        version = kwargs.get("version", None)

        # 获取草稿
        if version:
            draft = await self.drafts.get_draft(project_id, chapter, version)
        else:
            draft = await self.drafts.get_latest_draft(project_id, chapter)

        if not draft:
            return {"success": False, "error": "草稿不存在"}

        # 收集参考信息
        context_parts = []

        # 场景简报
        brief = await self.drafts.get_brief(project_id, chapter)
        if brief:
            context_parts.append(f"【章节目标】{brief.goal}")
            context_parts.append(f"【禁止事项】{', '.join(brief.forbidden)}")

        # 角色设定
        char_names = await self.cards.list_characters(project_id)
        for name in char_names[:5]:
            card = await self.cards.get_character(project_id, name)
            if card:
                context_parts.append(
                    f"【{card.name}】性格：{', '.join(card.personality[:3])}，"
                    f"边界：{', '.join(card.boundaries[:2]) if card.boundaries else '无'}"
                )

        # 事实表
        facts = await self.canon.get_facts(project_id)
        for f in facts[-5:]:
            context_parts.append(f"【已知事实】{f.statement}")

        # 规则
        rules = await self.cards.get_rules(project_id)
        if rules and rules.donts:
            context_parts.append(f"【规则-禁止】{', '.join(rules.donts[:5])}")

        context = "\n".join(context_parts)

        # 审核
        prompt = f"""请审核以下草稿：

{draft.content[:4000]}

请检查：
1. 是否与设定矛盾
2. 角色言行是否符合人设
3. 情节是否合理
4. 是否完成了章节目标"""

        response = await self.chat(prompt, context)

        # 解析问题（简化处理，实际应解析 YAML）
        issues = []
        score = 0.8

        # 尝试提取评分
        score_text = self.parse_xml_tag(response, "score")
        if score_text:
            try:
                score = float(score_text.strip())
            except:
                pass

        summary = self.parse_xml_tag(response, "summary") or "审核完成"

        review = Review(
            chapter=chapter,
            draft_version=draft.version,
            issues=issues,
            overall_score=score,
            summary=summary
        )

        await self.drafts.save_review(project_id, review)

        return {
            "success": True,
            "review": review,
            "raw": response
        }
