"""
事实表存储：事实、时间线、角色状态
"""

import re
from typing import List, Optional, Callable

from app.models.canon import Fact, TimelineEvent, CharacterState
from app.storage.base import BaseStorage
from app.utils.helpers import generate_id


class CanonStorage(BaseStorage):
    """事实表存储"""

    def __init__(self, data_dir: str = None):
        """初始化事实表存储，如果没有指定 data_dir 则使用配置中的默认值"""
        if data_dir is None:
            from app.config import get_config
            config = get_config()
            data_dir = str(config.data_dir)
        super().__init__(data_dir)

    # ========== 章节排序工具 ==========

    def _chapter_sort_key(self, chapter: str) -> tuple:
        """生成章节排序键，与 DraftStorage 保持一致"""
        cn_num_map = {
            '零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000, '万': 10000
        }

        def cn_to_num(cn_str: str) -> int:
            if not cn_str:
                return 0
            result = 0
            temp = 0
            for char in cn_str:
                if char in cn_num_map:
                    val = cn_num_map[char]
                    if val >= 10:
                        if temp == 0:
                            temp = 1
                        result += temp * val
                        temp = 0
                    else:
                        temp = temp * 10 + val
            result += temp
            return result if result > 0 else -1

        # 1. 匹配 "第X章" 格式（中文数字）
        match = re.match(r'第([零〇一二三四五六七八九十百千万]+)章', chapter)
        if match:
            return (2, cn_to_num(match.group(1)), chapter)

        # 2. 匹配 "第X章" 格式（阿拉伯数字）
        match = re.match(r'第(\d+)章', chapter)
        if match:
            return (2, int(match.group(1)), chapter)

        # 3. 匹配 "chX" 格式
        match = re.match(r'ch(\d+)', chapter, re.IGNORECASE)
        if match:
            return (2, int(match.group(1)), chapter)

        # 4. 匹配 "Chapter X" 格式
        match = re.match(r'chapter\s*(\d+)', chapter, re.IGNORECASE)
        if match:
            return (2, int(match.group(1)), chapter)

        # 5. 匹配纯数字开头
        match = re.match(r'(\d+)', chapter)
        if match:
            return (2, int(match.group(1)), chapter)

        # 6. 特殊章节（序章、楔子等）排最前面
        special_order = {'序章': 0, '楔子': 1, '引子': 2, '序言': 3, '前言': 4}
        for key, order in special_order.items():
            if key in chapter:
                return (1, order, chapter)

        # 7. 其他按字母顺序
        return (3, 0, chapter)

    def _sort_by_chapter(self, items: List, get_chapter: Callable) -> List:
        """按章节顺序排序"""
        return sorted(items, key=lambda x: self._chapter_sort_key(get_chapter(x)))

    # ========== 事实 ==========

    async def get_facts(self, project_id: str) -> List[Fact]:
        """获取所有事实（按章节排序）"""
        path = self._get_project_dir(project_id) / "canon" / "facts.jsonl"
        items = await self.read_jsonl(path)
        facts = [Fact(**item) for item in items]
        return self._sort_by_chapter(facts, lambda f: f.source)

    async def get_facts_for_writing(
        self,
        project_id: str,
        current_chapter: str,
        characters: List[str] = None,
        limit: int = 20
    ) -> List[Fact]:
        """
        获取写作时需要的事实（智能筛选）

        筛选策略：
        1. 所有 critical 重要性的事实
        2. 与当前出场角色相关的事实
        3. 按章节顺序排列，优先保留早期章节的基础设定
        """
        all_facts = await self.get_facts(project_id)
        characters = characters or []
        characters_lower = [c.lower() for c in characters]

        # 分类
        critical_facts = []
        character_related = []
        other_facts = []

        for fact in all_facts:
            # critical 重要性
            if fact.importance == "critical":
                critical_facts.append(fact)
            # 与出场角色相关
            elif characters and (
                any(c.lower() in characters_lower for c in fact.characters) or
                any(c in fact.statement for c in characters)
            ):
                character_related.append(fact)
            else:
                other_facts.append(fact)

        # 合并：critical 全部 + 角色相关 + 其他补充
        result = critical_facts.copy()
        remaining = limit - len(result)

        if remaining > 0:
            result.extend(character_related[:remaining])
            remaining = limit - len(result)

        if remaining > 0:
            # 其他事实取最近的
            result.extend(other_facts[-remaining:])

        return result

    async def add_fact(self, project_id: str, fact: Fact) -> Fact:
        """添加事实"""
        if not fact.id:
            fact.id = generate_id("F")
        path = self._get_project_dir(project_id) / "canon" / "facts.jsonl"
        await self.append_jsonl(path, fact.model_dump())
        return fact

    async def update_fact(self, project_id: str, fact: Fact) -> bool:
        """更新事实（用于修改同一章节的事实）"""
        path = self._get_project_dir(project_id) / "canon" / "facts.jsonl"
        items = await self.read_jsonl(path)

        updated = False
        for i, item in enumerate(items):
            if item.get("id") == fact.id:
                items[i] = fact.model_dump()
                updated = True
                break

        if updated:
            await self.write_jsonl(path, items)
        return updated

    async def remove_facts_by_source(self, project_id: str, source: str) -> int:
        """删除指定来源章节的所有事实（用于重新提取）"""
        path = self._get_project_dir(project_id) / "canon" / "facts.jsonl"
        items = await self.read_jsonl(path)

        original_count = len(items)
        items = [item for item in items if item.get("source") != source]

        await self.write_jsonl(path, items)
        return original_count - len(items)

    async def find_fact(self, project_id: str, fact_id: str) -> Optional[Fact]:
        """查找事实"""
        facts = await self.get_facts(project_id)
        for f in facts:
            if f.id == fact_id:
                return f
        return None

    # ========== 时间线 ==========

    async def get_timeline(self, project_id: str) -> List[TimelineEvent]:
        """获取所有时间线事件（按章节排序）"""
        path = self._get_project_dir(project_id) / "canon" / "timeline.jsonl"
        items = await self.read_jsonl(path)
        events = [TimelineEvent(**item) for item in items]
        return self._sort_by_chapter(events, lambda e: e.source)

    async def get_timeline_for_writing(
        self,
        project_id: str,
        current_chapter: str,
        characters: List[str] = None,
        limit: int = 15
    ) -> List[TimelineEvent]:
        """
        获取写作时需要的时间线（智能筛选）

        筛选策略：
        1. 与当前出场角色相关的事件
        2. 按时间顺序保留
        """
        all_events = await self.get_timeline(project_id)
        characters = characters or []

        if not characters:
            return all_events[-limit:]

        # 筛选与角色相关的事件
        related = []
        other = []

        for event in all_events:
            if any(c in event.participants for c in characters):
                related.append(event)
            else:
                other.append(event)

        # 角色相关 + 其他补充
        result = related.copy()
        remaining = limit - len(result)

        if remaining > 0:
            result.extend(other[-remaining:])

        # 按章节顺序排列
        return self._sort_by_chapter(result, lambda e: e.source)

    async def get_facts_for_review(
        self,
        project_id: str,
        current_chapter: str,
        characters: List[str] = None,
        limit: int = 50
    ) -> List[Fact]:
        """
        获取审稿时需要的事实（比写作时更全面）

        筛选策略：
        1. 所有 critical 重要性的事实（不计入 limit）
        2. 与当前出场角色相关的事实
        3. 高置信度（>=0.8）的事实优先
        4. 按章节顺序排列
        """
        all_facts = await self.get_facts(project_id)
        characters = characters or []
        characters_lower = [c.lower() for c in characters]

        # 分类
        critical_facts = []
        high_confidence_related = []
        other_related = []
        other_facts = []

        for fact in all_facts:
            is_related = characters and (
                any(c.lower() in characters_lower for c in fact.characters) or
                any(c in fact.statement for c in characters)
            )

            if fact.importance == "critical":
                critical_facts.append(fact)
            elif is_related and fact.confidence >= 0.8:
                high_confidence_related.append(fact)
            elif is_related:
                other_related.append(fact)
            elif fact.confidence >= 0.8:
                other_facts.append(fact)

        # 合并：critical 全部（不计入 limit）+ 高置信度相关 + 其他相关 + 其他高置信度
        result = critical_facts.copy()
        remaining = limit

        if remaining > 0:
            result.extend(high_confidence_related[:remaining])
            remaining = limit - len(high_confidence_related)

        if remaining > 0:
            result.extend(other_related[:remaining])
            remaining -= len(other_related[:remaining])

        if remaining > 0:
            result.extend(other_facts[:remaining])

        # 按章节顺序排序
        return self._sort_by_chapter(result, lambda f: f.source)

    async def get_timeline_for_review(
        self,
        project_id: str,
        current_chapter: str,
        characters: List[str] = None,
        limit: int = 30
    ) -> List[TimelineEvent]:
        """
        获取审稿时需要的时间线（比写作时更全面）

        筛选策略：
        1. 与当前出场角色相关的事件优先
        2. 按章节顺序保留
        """
        all_events = await self.get_timeline(project_id)
        characters = characters or []

        if not characters:
            # 无角色信息时，取最近的事件
            return all_events[-limit:] if len(all_events) > limit else all_events

        # 筛选与角色相关的事件
        related = []
        other = []

        for event in all_events:
            if any(c in event.participants for c in characters):
                related.append(event)
            else:
                other.append(event)

        # 角色相关全部 + 其他补充
        result = related.copy()
        remaining = limit - len(result)

        if remaining > 0:
            result.extend(other[-remaining:])

        return self._sort_by_chapter(result, lambda e: e.source)

    async def add_timeline_event(self, project_id: str, event: TimelineEvent) -> TimelineEvent:
        """添加时间线事件"""
        if not event.id:
            event.id = generate_id("T")
        path = self._get_project_dir(project_id) / "canon" / "timeline.jsonl"
        await self.append_jsonl(path, event.model_dump())
        return event

    async def remove_timeline_by_source(self, project_id: str, source: str) -> int:
        """删除指定来源章节的所有时间线事件"""
        path = self._get_project_dir(project_id) / "canon" / "timeline.jsonl"
        items = await self.read_jsonl(path)

        original_count = len(items)
        items = [item for item in items if item.get("source") != source]

        await self.write_jsonl(path, items)
        return original_count - len(items)

    # ========== 角色状态 ==========

    async def get_character_states(self, project_id: str) -> List[CharacterState]:
        """获取所有角色状态（按章节排序）"""
        path = self._get_project_dir(project_id) / "canon" / "states.jsonl"
        items = await self.read_jsonl(path)
        states = [CharacterState(**item) for item in items]
        return self._sort_by_chapter(states, lambda s: s.chapter)

    async def get_latest_states(
        self,
        project_id: str,
        characters: List[str] = None
    ) -> List[CharacterState]:
        """
        获取角色的最新状态

        如果指定了 characters，只返回这些角色的状态
        否则返回所有角色的最新状态
        """
        all_states = await self.get_character_states(project_id)

        # 每个角色只保留最新的状态
        latest: dict[str, CharacterState] = {}
        for state in all_states:
            latest[state.character] = state

        if characters:
            return [latest[c] for c in characters if c in latest]

        return list(latest.values())

    async def get_character_state(self, project_id: str, character: str) -> Optional[CharacterState]:
        """获取某角色的最新状态"""
        states = await self.get_character_states(project_id)
        # 返回该角色的最后一条状态（已按章节排序）
        for state in reversed(states):
            if state.character == character:
                return state
        return None

    async def update_character_state(self, project_id: str, state: CharacterState) -> CharacterState:
        """更新角色状态（追加新状态）"""
        path = self._get_project_dir(project_id) / "canon" / "states.jsonl"
        await self.append_jsonl(path, state.model_dump())
        return state

    async def remove_states_by_chapter(self, project_id: str, chapter: str) -> int:
        """删除指定章节的所有角色状态"""
        path = self._get_project_dir(project_id) / "canon" / "states.jsonl"
        items = await self.read_jsonl(path)

        original_count = len(items)
        items = [item for item in items if item.get("chapter") != chapter]

        await self.write_jsonl(path, items)
        return original_count - len(items)

    # ========== 批量操作 ==========

    async def clear_canon(self, project_id: str) -> None:
        """清空事实表（谨慎使用）"""
        canon_dir = self._get_project_dir(project_id) / "canon"
        for f in ["facts.jsonl", "timeline.jsonl", "states.jsonl"]:
            path = canon_dir / f
            if path.exists():
                path.unlink()

    async def rebuild_chapter_canon(self, project_id: str, chapter: str) -> dict:
        """
        重建某章节的事实表（删除旧的，准备重新提取）
        返回删除的数量
        """
        facts_removed = await self.remove_facts_by_source(project_id, chapter)
        timeline_removed = await self.remove_timeline_by_source(project_id, chapter)
        states_removed = await self.remove_states_by_chapter(project_id, chapter)

        return {
            "facts_removed": facts_removed,
            "timeline_removed": timeline_removed,
            "states_removed": states_removed
        }
