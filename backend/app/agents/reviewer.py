"""
审稿人 Agent
负责：审核草稿质量，检查一致性问题，检测与已知事实的冲突
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
5. conflict - 与已知事实的冲突

问题严重程度：
- critical: 严重问题，必须修改（如与已知事实直接矛盾）
- major: 较大问题，建议修改
- minor: 小问题，可选修改

输出格式：
<issues>
ISSUE|类别|严重程度|问题描述|修改建议
</issues>
<conflicts>
CONFLICT|冲突的事实|草稿中的矛盾内容|建议修改方案
</conflicts>
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

        # 事实表 - 用于冲突检测
        facts = await self.canon.get_facts(project_id)
        facts_for_check = []
        for f in facts:
            context_parts.append(f"【已知事实】{f.statement}（来源：{f.source}，置信度：{f.confidence}）")
            facts_for_check.append(f.statement)

        # 时间线事件 - 用于时序冲突检测
        timeline = await self.canon.get_timeline(project_id)
        for event in timeline[-10:]:
            context_parts.append(f"【时间线】{event.time}：{event.event}（{', '.join(event.participants)}）")

        # 角色状态 - 用于状态冲突检测
        states = await self.canon.get_character_states(project_id)
        for state in states[-5:]:
            state_desc = f"【{state.character}状态@{state.chapter}】"
            if state.location:
                state_desc += f"位置：{state.location}，"
            if state.emotional_state:
                state_desc += f"情绪：{state.emotional_state}，"
            if state.injuries:
                state_desc += f"伤势：{', '.join(state.injuries)}"
            context_parts.append(state_desc)

        # 规则
        rules = await self.cards.get_rules(project_id)
        if rules and rules.donts:
            context_parts.append(f"【规则-禁止】{', '.join(rules.donts[:5])}")

        context = "\n".join(context_parts)

        # 审核（包含冲突检测）
        prompt = f"""请审核以下草稿，特别注意与已知事实的冲突：

{draft.content[:4000]}

请检查：
1. 是否与设定矛盾
2. 角色言行是否符合人设
3. 情节是否合理
4. 是否完成了章节目标
5. **重点**：是否与【已知事实】、【时间线】、【角色状态】存在冲突

如果发现与已知事实冲突，请在 <conflicts> 中明确指出：
- 哪个已知事实被违反
- 草稿中的哪段内容与之矛盾
- 建议如何修改

输出格式（每项一行）：
<issues>
ISSUE|类别|严重程度|问题描述|修改建议
</issues>
<conflicts>
CONFLICT|冲突的事实|草稿中的矛盾内容|建议修改方案
</conflicts>
<score>0.0-1.0</score>
<summary>总体评价</summary>"""

        response = await self.chat(prompt, context)

        # 解析问题
        issues: List[ReviewIssue] = []
        issues_text = self.parse_xml_tag(response, "issues")
        if issues_text:
            for line in issues_text.strip().split("\n"):
                line = line.strip()
                if line.startswith("ISSUE|"):
                    parts = line.split("|")
                    if len(parts) >= 5:
                        issues.append(ReviewIssue(
                            category=parts[1],
                            severity=parts[2],
                            problem=parts[3],
                            suggestion=parts[4]
                        ))

        # 解析冲突
        conflicts: List[Dict[str, str]] = []
        conflicts_text = self.parse_xml_tag(response, "conflicts")
        if conflicts_text:
            for line in conflicts_text.strip().split("\n"):
                line = line.strip()
                if line.startswith("CONFLICT|"):
                    parts = line.split("|")
                    if len(parts) >= 4:
                        conflicts.append({
                            "fact": parts[1],
                            "contradiction": parts[2],
                            "suggestion": parts[3]
                        })
                        # 冲突也作为 critical issue 添加
                        issues.append(ReviewIssue(
                            category="conflict",
                            severity="critical",
                            problem=f"与已知事实冲突：{parts[1]} vs {parts[2]}",
                            suggestion=parts[3]
                        ))

        # 提取评分
        score = 0.8
        score_text = self.parse_xml_tag(response, "score")
        if score_text:
            try:
                score = float(score_text.strip())
            except:
                pass

        # 如果有冲突，降低评分
        if conflicts:
            score = min(score, 0.5)  # 有冲突时评分上限为 0.5

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
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
            "raw": response
        }
