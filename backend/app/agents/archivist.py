"""
资料员 Agent
负责：生成场景简报、提取事实、生成章节摘要
"""

import asyncio
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

        # 并行获取基础数据
        char_names_task = None
        if not characters:
            char_names_task = self.cards.list_characters(project_id)

        world_names_task = self.cards.list_world_cards(project_id)
        style_task = self.cards.get_style(project_id)
        rules_task = self.cards.get_rules(project_id)
        summaries_task = self.drafts.get_previous_summaries(project_id, chapter, limit=3)
        facts_task = self.canon.get_facts(project_id)

        # 并行执行所有任务
        tasks = [world_names_task, style_task, rules_task, summaries_task, facts_task]
        if char_names_task:
            tasks.append(char_names_task)

        results = await asyncio.gather(*tasks)

        world_names = results[0]
        style = results[1]
        rules = results[2]
        summaries = results[3]
        facts = results[4]
        char_names = results[5] if char_names_task else characters

        # 并行获取角色卡和世界观卡详情
        char_card_tasks = [
            self.cards.get_character(project_id, name)
            for name in char_names[:10]
        ]
        world_card_tasks = [
            self.cards.get_world_card(project_id, name)
            for name in world_names[:10]
        ]

        all_card_results = await asyncio.gather(*char_card_tasks, *world_card_tasks)

        char_cards = all_card_results[:len(char_card_tasks)]
        world_cards = all_card_results[len(char_card_tasks):]

        # 收集上下文
        context_parts = []

        # 角色卡
        for card in char_cards:
            if card:
                context_parts.append(f"【角色】{card.name}: {card.identity}, 性格: {', '.join(card.personality)}")

        # 世界观
        for card in world_cards:
            if card:
                context_parts.append(f"【设定】{card.name}: {card.description}")

        # 前文摘要
        for s in summaries:
            context_parts.append(f"【{s.chapter}摘要】{s.summary}")

        # 最近事实
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
        """从章节内容提取事实、时间线事件、角色状态"""
        prompt = f"""从以下章节内容中提取**对后续写作有参考价值**的关键信息：

章节：{chapter}

{content[:3000]}

## 提取原则（重要！）

### 事实提取标准：
**只提取对后续章节写作有约束力或参考价值的事实，忽略临时性动作和环境描写。**

✅ 应该提取的事实：
- 角色身份/背景揭示（如"张三是前朝皇室后裔"）
- 重要决定/承诺（如"张三决定前往京城"、"李四答应帮助张三"）
- 关系变化（如"张三与李四结为兄弟"、"王五背叛了组织"）
- 能力/技能展示（如"张三展现出火系法术天赋"）
- 重要物品获得/失去（如"张三获得了上古神剑"）
- 世界观设定（如"这个世界的修炼分为九个境界"）
- 重大事件结果（如"黑风寨被剿灭"、"王城陷落"）

❌ 不应该提取的事实：
- 临时动作（如"张三走在路上"、"李四攥紧拳头"、"王五眯起眼睛"）
- 瞬时情绪表达（如"张三感到一阵愤怒"）——这类放到角色状态中
- 纯环境描写（如"天空飘着白云"、"远处有几座山丘"）
- 对话中的客套/过渡语

### 事实合并原则：
- 相关的信息应合并为一条事实，避免碎片化
- 例如：地理环境描写可合并为"XX地区的地貌特征为：荒凉土丘、人烟稀少、有蜿蜒山路通往群山"
- 例如：角色的多个特征可合并为"张三的特点：性格沉稳、擅长剑术、背负血海深仇"

### 数量控制：
- 每章事实数量控制在 **5-15 条**，宁缺毋滥
- 优先保留 critical 和 normal 级别的事实
- minor 级别只保留确实有参考价值的

## 输出格式

<facts>
FACT|事实描述（可以是完整的一段话）|置信度(0.0-1.0)|相关角色1,角色2|重要性(critical/normal/minor)
</facts>
<timeline>
EVENT|时间|事件描述|参与者1,参与者2|地点
</timeline>
<states>
STATE|角色名|位置|情绪状态|目标1,目标2|伤势1,伤势2|物品1,物品2|关系人1:关系,关系人2:关系
</states>

## 重要性分级说明：
- critical: 核心设定，必须记住（角色身份、世界观规则、重大转折）
- normal: 一般事实，有参考价值（关系变化、重要决定、能力展示）
- minor: 细节补充，可选记录（次要地点、次要物品）

## 角色状态说明：
- 只记录本章**结束时**角色的状态快照
- 情绪状态记录持续性的情绪基调，不是瞬时反应
- 物品只记录关键道具，不记录普通物品"""

        response = await self.chat(prompt)

        # 解析响应
        extracted_facts: List[Fact] = []
        extracted_timeline: List[TimelineEvent] = []
        extracted_states: List[CharacterState] = []

        # 解析事实
        facts_text = self.parse_xml_tag(response, "facts")
        if facts_text:
            for line in facts_text.strip().split("\n"):
                line = line.strip()
                if line.startswith("FACT|"):
                    parts = line.split("|")
                    if len(parts) >= 2:
                        try:
                            confidence = float(parts[2]) if len(parts) > 2 and parts[2] else 1.0
                        except ValueError:
                            confidence = 1.0
                        # 解析相关角色
                        characters = []
                        if len(parts) > 3 and parts[3]:
                            characters = [c.strip() for c in parts[3].split(",") if c.strip()]
                        # 解析重要性
                        importance = "normal"
                        if len(parts) > 4 and parts[4]:
                            imp = parts[4].strip().lower()
                            if imp in ["critical", "normal", "minor"]:
                                importance = imp
                        extracted_facts.append(Fact(
                            statement=parts[1],
                            source=chapter,
                            confidence=min(1.0, max(0.0, confidence)),
                            characters=characters,
                            importance=importance
                        ))

        # 解析时间线
        timeline_text = self.parse_xml_tag(response, "timeline")
        if timeline_text:
            for line in timeline_text.strip().split("\n"):
                line = line.strip()
                if line.startswith("EVENT|"):
                    parts = line.split("|")
                    if len(parts) >= 3:
                        participants = parts[3].split(",") if len(parts) > 3 and parts[3] else []
                        location = parts[4] if len(parts) > 4 else ""
                        extracted_timeline.append(TimelineEvent(
                            time=parts[1],
                            event=parts[2],
                            participants=[p.strip() for p in participants if p.strip()],
                            location=location,
                            source=chapter
                        ))

        # 解析角色状态
        states_text = self.parse_xml_tag(response, "states")
        if states_text:
            for line in states_text.strip().split("\n"):
                line = line.strip()
                if line.startswith("STATE|"):
                    parts = line.split("|")
                    if len(parts) >= 2:
                        goals = parts[4].split(",") if len(parts) > 4 and parts[4] else []
                        injuries = parts[5].split(",") if len(parts) > 5 and parts[5] else []
                        inventory = parts[6].split(",") if len(parts) > 6 and parts[6] else []
                        # 解析关系：格式为 "角色名:关系,角色名:关系"
                        relationships: Dict[str, str] = {}
                        if len(parts) > 7 and parts[7]:
                            for rel in parts[7].split(","):
                                rel = rel.strip()
                                if ":" in rel:
                                    rel_name, rel_desc = rel.split(":", 1)
                                    relationships[rel_name.strip()] = rel_desc.strip()
                        extracted_states.append(CharacterState(
                            character=parts[1],
                            chapter=chapter,
                            location=parts[2] if len(parts) > 2 else "",
                            emotional_state=parts[3] if len(parts) > 3 else "",
                            goals=[g.strip() for g in goals if g.strip()],
                            injuries=[i.strip() for i in injuries if i.strip()],
                            inventory=[i.strip() for i in inventory if i.strip()],
                            relationships=relationships
                        ))

        return {
            "success": True,
            "facts": extracted_facts,
            "timeline": extracted_timeline,
            "states": extracted_states,
            "raw": response
        }

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
