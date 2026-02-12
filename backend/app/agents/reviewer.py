"""
审稿人 Agent
负责：审核草稿质量，检查一致性问题，检测与已知事实的冲突
"""

import logging
from typing import Dict, Any, List

from app.agents.base import BaseAgent
from app.models.draft import Review, ReviewIssue
from app.utils.helpers import smart_truncate_content
from app.storage.ontology import OntologyStorage

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    """审稿人"""

    def __init__(
        self,
        card_storage: "CardStorage" = None,
        canon_storage: "CanonStorage" = None,
        draft_storage: "DraftStorage" = None
    ):
        super().__init__(card_storage, canon_storage, draft_storage)
        self.ontology_storage = OntologyStorage()

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

        # 本体上下文（结构化数据，更高效的一致性检查）
        ontology_context = await self.ontology_storage.get_review_context(
            project_id, characters=None, token_budget=3000
        )
        if ontology_context.strip():
            context_parts.append(f"【本体上下文（核心约束）】\n{ontology_context}")

        # 场景简报
        brief = await self.drafts.get_brief(project_id, chapter)
        if brief:
            context_parts.append(f"【章节目标】{brief.goal}")
            context_parts.append(f"【禁止事项】{', '.join(brief.forbidden)}")

        # 角色设定 - 提取出场角色名用于智能筛选
        char_names = await self.cards.list_characters(project_id)
        current_characters = []
        for name in char_names[:5]:
            card = await self.cards.get_character(project_id, name)
            if card:
                current_characters.append(card.name)
                context_parts.append(
                    f"【{card.name}】性格：{', '.join(card.personality[:3])}，"
                    f"说话风格：{card.speech_pattern}，"
                    f"边界：{', '.join(card.boundaries[:2]) if card.boundaries else '无'}"
                )

        # 世界观设定
        world_names = await self.cards.list_world_cards(project_id)
        for name in world_names[:8]:
            world = await self.cards.get_world_card(project_id, name)
            if world:
                context_parts.append(f"【世界观-{world.category}】{world.name}：{world.description[:150]}")

        # 文风卡
        style = await self.cards.get_style(project_id)
        if style:
            context_parts.append(f"【文风要求】叙事距离：{style.narrative_distance}，节奏：{style.pacing}")
            if style.sentence_style:
                context_parts.append(f"【句式要求】{style.sentence_style}")
            if style.vocabulary:
                context_parts.append(f"【推荐词汇】{', '.join(style.vocabulary[:15])}")
            if style.taboo_words:
                context_parts.append(f"【禁用词汇】{', '.join(style.taboo_words[:15])}")

        # 事实表 - 用于冲突检测（智能筛选：critical全部 + 角色相关 + 高置信度）
        facts = await self.canon.get_facts_for_review(
            project_id,
            chapter,
            characters=current_characters,
            limit=50
        )
        for f in facts:
            importance_mark = "⚠️" if f.importance == "critical" else ""
            context_parts.append(f"【已知事实{importance_mark}】{f.statement}（来源：{f.source}，置信度：{f.confidence}）")

        # 时间线事件 - 用于时序冲突检测（智能筛选：角色相关优先）
        timeline = await self.canon.get_timeline_for_review(
            project_id,
            chapter,
            characters=current_characters,
            limit=30
        )
        for event in timeline:
            context_parts.append(f"【时间线】{event.time}：{event.event}（{', '.join(event.participants)}，来源：{event.source}）")

        # 角色状态 - 用于状态冲突检测（出场角色的最新状态）
        states = await self.canon.get_latest_states(project_id, characters=current_characters)
        for state in states:
            state_desc = f"【{state.character}状态@{state.chapter}】"
            if state.location:
                state_desc += f"位置：{state.location}，"
            if state.emotional_state:
                state_desc += f"情绪：{state.emotional_state}，"
            if state.injuries:
                state_desc += f"伤势：{', '.join(state.injuries)}，"
            if state.inventory:
                state_desc += f"持有物品：{', '.join(state.inventory)}，"
            if state.relationships:
                rel_strs = [f"{k}({v})" for k, v in state.relationships.items()]
                state_desc += f"人物关系：{', '.join(rel_strs)}"
            context_parts.append(state_desc)

        # 规则（完整）
        rules = await self.cards.get_rules(project_id)
        if rules:
            if rules.dos:
                context_parts.append(f"【规则-必须遵守】{', '.join(rules.dos)}")
            if rules.donts:
                context_parts.append(f"【规则-禁止】{', '.join(rules.donts)}")
            if rules.quality_standards:
                context_parts.append(f"【质量标准】{', '.join(rules.quality_standards)}")

        context = "\n".join(context_parts)

        # 使用智能截断，保留首尾和中间采样，避免只看到开头
        truncated_draft = smart_truncate_content(draft.content, budget=4000)

        # 审核（包含冲突检测）
        prompt = f"""请审核以下草稿，特别注意与已知事实的冲突：

{truncated_draft}

请检查：
1. 是否与角色设定矛盾（性格、说话风格、边界）
2. 是否与世界观设定矛盾（地理、体系、规则等）
3. 角色言行是否符合人设
4. 情节是否合理，是否完成了章节目标
5. 文风是否符合要求（叙事距离、节奏、句式、是否使用了禁用词汇）
6. 是否违反了【规则-必须遵守】或【规则-禁止】
7. 是否达到了【质量标准】
8. **重点**：是否与【已知事实】、【时间线】、【角色状态】存在冲突

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
        # logger.info(f"[Reviewer] Raw conflicts_text: '{conflicts_text}'")
        if conflicts_text:
            for line in conflicts_text.strip().split("\n"):
                line = line.strip()
                if line.startswith("CONFLICT|"):
                    parts = line.split("|")
                    if len(parts) >= 4:
                        fact = parts[1].strip()
                        contradiction = parts[2].strip()
                        suggestion = parts[3].strip()
                        # 验证冲突内容不为空且不是占位符
                        # LLM 有时会返回空的或占位符式的冲突
                        if (fact and contradiction and suggestion
                            and len(fact) > 2 and len(contradiction) > 2
                            and fact not in ["无", "暂无", "无冲突", "N/A", "-"]
                            and contradiction not in ["无", "暂无", "无冲突", "N/A", "-"]):
                            conflicts.append({
                                "fact": fact,
                                "contradiction": contradiction,
                                "suggestion": suggestion
                            })
                            # 冲突也作为 critical issue 添加
                            issues.append(ReviewIssue(
                                category="conflict",
                                severity="critical",
                                problem=f"与已知事实冲突：{fact} vs {contradiction}",
                                suggestion=suggestion
                            ))
                            # logger.info(f"[Reviewer] Valid conflict found: {fact[:50]}...")
                        else:
                            pass  # logger.info(f"[Reviewer] Skipped invalid/placeholder conflict: {line[:80]}")
        # logger.info(f"[Reviewer] Parsed conflicts count: {len(conflicts)}")

        # 提取评分
        score = 0.8
        score_text = self.parse_xml_tag(response, "score")
        # logger.info(f"[Reviewer] Raw score_text: '{score_text}'")
        if score_text:
            try:
                # 处理可能的格式问题，比如 "0.85分" 或 "85%"
                cleaned_score = score_text.strip()
                # 移除可能的后缀
                for suffix in ["分", "%", "分数"]:
                    cleaned_score = cleaned_score.replace(suffix, "")
                cleaned_score = cleaned_score.strip()

                parsed_score = float(cleaned_score)
                # 如果是百分制，转换为小数
                if parsed_score > 1:
                    parsed_score = parsed_score / 100
                score = max(0.0, min(1.0, parsed_score))
                # logger.info(f"[Reviewer] Parsed score: {score}")
            except Exception as e:
                logger.warning(f"[Reviewer] Failed to parse score '{score_text}': {e}")
        else:
            logger.warning(f"[Reviewer] No score tag found in response")

        # 如果有冲突，根据冲突数量降低评分，但不要太狠
        # 重要：不再硬性限制上限，而是根据冲突数量扣分
        # 这样即使有轻微冲突，如果整体质量高，仍然可以通过
        if conflicts:
            conflict_penalty = len(conflicts) * 0.05  # 每个冲突扣 0.05
            conflict_penalty = min(conflict_penalty, 0.2)  # 最多扣 0.2
            old_score = score
            score = max(score - conflict_penalty, 0.5)  # 下限 0.5
            # logger.info(f"[Reviewer] Found {len(conflicts)} conflicts, score adjusted: {old_score:.2f} -> {score:.2f}")

        summary = self.parse_xml_tag(response, "summary") or "审核完成"

        # 程序化规则校验（补充 LLM 审稿）
        programmatic_issues = self._programmatic_check(
            content=draft.content,
            style=style,
            rules=rules,
            brief=brief,
            characters=current_characters,
            target_words=brief.target_words if brief and hasattr(brief, "target_words") else 0
        )
        # logger.info(f"[Reviewer] Programmatic issues count: {len(programmatic_issues)}")
        # for pi in programmatic_issues:
        #     logger.info(f"[Reviewer]   - [{pi.severity}] {pi.category}: {pi.problem}")

        # 合并程序化校验发现的问题（放在最前面，因为这些是确定性问题）
        if programmatic_issues:
            issues = programmatic_issues + issues
            # 如果有 major 级别的程序化问题，也要降低评分
            # 但不要降得太狠，每个 major 问题降 0.05，下限为 0.55
            major_count = sum(1 for i in programmatic_issues if i.severity == "major")
            if major_count > 0:
                old_score = score
                penalty = min(major_count * 0.05, 0.25)  # 最多降 0.25
                score = max(score - penalty, 0.55)  # 下限 0.55，确保还有机会通过
                # logger.info(f"[Reviewer] Score adjusted for {major_count} major issues: {old_score:.2f} -> {score:.2f}")

        # logger.info(f"[Reviewer] Final score: {score:.2f}, total issues: {len(issues)}")

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

    def _programmatic_check(
        self,
        content: str,
        style: Any,
        rules: Any,
        brief: Any,
        characters: List[str],
        target_words: int = 0
    ) -> List[ReviewIssue]:
        """
        程序化规则校验：检查确定性规则，作为 LLM 审稿的补充

        这些检查不依赖 LLM 的判断，是 100% 确定的规则违反
        """
        issues = []

        # 1. 禁用词汇检查
        if style and style.taboo_words:
            for word in style.taboo_words:
                if word and word in content:
                    # 统计出现次数
                    count = content.count(word)
                    issues.append(ReviewIssue(
                        category="style",
                        severity="major",
                        problem=f"使用了禁用词汇「{word}」（出现 {count} 次）",
                        suggestion=f"请替换或删除禁用词汇「{word}」"
                    ))

        # 2. 规则卡-禁止事项检查（精确匹配关键词）
        # 注意：这种简单的关键词匹配容易产生误报，所以只作为提醒（minor），不作为严重问题
        if rules and rules.donts:
            for dont in rules.donts:
                # 提取关键词（去掉"不要"、"禁止"等前缀）
                keywords = self._extract_keywords_from_rule(dont)
                matched_keywords = []
                for keyword in keywords:
                    if keyword and len(keyword) >= 2 and keyword in content:
                        matched_keywords.append(keyword)
                # 只有当多个关键词都匹配时才报告（降低误报率）
                if len(matched_keywords) >= 2:
                    issues.append(ReviewIssue(
                        category="rules",
                        severity="minor",  # 降级为 minor，因为关键词匹配可能有误报
                        problem=f"可能违反禁止规则「{dont}」（检测到关键词：{', '.join(matched_keywords)}）",
                        suggestion=f"请检查是否违反了「{dont}」这条规则"
                    ))

        # 3. 字数检查（如果有目标字数）
        if target_words > 0:
            actual_words = len(content)
            if actual_words < target_words * 0.7:
                issues.append(ReviewIssue(
                    category="plot",
                    severity="minor",
                    problem=f"字数不足：目标 {target_words} 字，实际 {actual_words} 字（{actual_words*100//target_words}%）",
                    suggestion="考虑扩展情节或增加细节描写"
                ))
            elif actual_words > target_words * 1.5:
                issues.append(ReviewIssue(
                    category="plot",
                    severity="minor",
                    problem=f"字数超标：目标 {target_words} 字，实际 {actual_words} 字（{actual_words*100//target_words}%）",
                    suggestion="考虑精简内容或拆分章节"
                ))

        # 4. 出场角色检查（设定出场但未在文中提及）
        if characters and brief:
            brief_characters = [c.get("name", "") for c in (brief.characters or [])] if hasattr(brief, "characters") else []
            for char_name in brief_characters:
                if char_name and char_name not in content:
                    issues.append(ReviewIssue(
                        category="character",
                        severity="minor",
                        problem=f"角色「{char_name}」设定出场但未在文中出现",
                        suggestion=f"请确认是否需要「{char_name}」出场，或在文中添加该角色"
                    ))

        # 5. 基础格式检查
        # 检查是否有大段重复内容（可能是粘贴错误）
        paragraphs = content.split('\n\n')
        seen_paragraphs = set()
        for para in paragraphs:
            para_normalized = para.strip()
            if len(para_normalized) > 50:  # 只检查较长的段落
                if para_normalized in seen_paragraphs:
                    issues.append(ReviewIssue(
                        category="consistency",
                        severity="major",
                        problem="检测到重复段落",
                        suggestion="请检查是否有误粘贴的重复内容"
                    ))
                    break  # 只报告一次
                seen_paragraphs.add(para_normalized)

        return issues

    def _extract_keywords_from_rule(self, rule: str) -> List[str]:
        """从规则描述中提取关键词"""
        # 移除常见的规则前缀
        prefixes = ["不要", "禁止", "不能", "不可以", "避免", "不得"]
        cleaned = rule
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break

        # 提取名词性关键词（简单实现：提取2-4字的词）
        import re
        keywords = re.findall(r'[\u4e00-\u9fff]{2,4}', cleaned)
        return keywords[:3]  # 最多返回3个关键词
