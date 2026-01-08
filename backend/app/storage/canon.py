"""
事实表存储：事实、时间线、角色状态
"""

from typing import List, Optional

from app.models.canon import Fact, TimelineEvent, CharacterState
from app.storage.base import BaseStorage
from app.utils.helpers import generate_id


class CanonStorage(BaseStorage):
    """事实表存储"""

    # ========== 事实 ==========

    async def get_facts(self, project_id: str) -> List[Fact]:
        """获取所有事实"""
        path = self._get_project_dir(project_id) / "canon" / "facts.jsonl"
        items = await self.read_jsonl(path)
        return [Fact(**item) for item in items]

    async def add_fact(self, project_id: str, fact: Fact) -> Fact:
        """添加事实"""
        if not fact.id:
            fact.id = generate_id("F")
        path = self._get_project_dir(project_id) / "canon" / "facts.jsonl"
        await self.append_jsonl(path, fact.model_dump())
        return fact

    async def find_fact(self, project_id: str, fact_id: str) -> Optional[Fact]:
        """查找事实"""
        facts = await self.get_facts(project_id)
        for f in facts:
            if f.id == fact_id:
                return f
        return None

    # ========== 时间线 ==========

    async def get_timeline(self, project_id: str) -> List[TimelineEvent]:
        """获取所有时间线事件"""
        path = self._get_project_dir(project_id) / "canon" / "timeline.jsonl"
        items = await self.read_jsonl(path)
        return [TimelineEvent(**item) for item in items]

    async def add_timeline_event(self, project_id: str, event: TimelineEvent) -> TimelineEvent:
        """添加时间线事件"""
        if not event.id:
            event.id = generate_id("T")
        path = self._get_project_dir(project_id) / "canon" / "timeline.jsonl"
        await self.append_jsonl(path, event.model_dump())
        return event

    # ========== 角色状态 ==========

    async def get_character_states(self, project_id: str) -> List[CharacterState]:
        """获取所有角色状态"""
        path = self._get_project_dir(project_id) / "canon" / "states.jsonl"
        items = await self.read_jsonl(path)
        return [CharacterState(**item) for item in items]

    async def get_character_state(self, project_id: str, character: str) -> Optional[CharacterState]:
        """获取某角色的最新状态"""
        states = await self.get_character_states(project_id)
        # 返回该角色的最后一条状态
        for state in reversed(states):
            if state.character == character:
                return state
        return None

    async def update_character_state(self, project_id: str, state: CharacterState) -> CharacterState:
        """更新角色状态（追加新状态）"""
        path = self._get_project_dir(project_id) / "canon" / "states.jsonl"
        await self.append_jsonl(path, state.model_dump())
        return state

    # ========== 批量操作 ==========

    async def clear_canon(self, project_id: str) -> None:
        """清空事实表（谨慎使用）"""
        canon_dir = self._get_project_dir(project_id) / "canon"
        for f in ["facts.jsonl", "timeline.jsonl", "states.jsonl"]:
            path = canon_dir / f
            if path.exists():
                path.unlink()
