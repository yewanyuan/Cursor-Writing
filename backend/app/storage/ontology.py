"""
本体存储：管理结构化的故事本体数据
"""

import logging
from typing import Optional, List

from app.models.ontology import (
    StoryOntology,
    CharacterGraph,
    CharacterNode,
    Relationship,
    RelationType,
    CharacterStatus,
    WorldOntology,
    WorldRule,
    Location,
    Faction,
    Timeline,
    TimelineEvent,
    EventType
)
from app.storage.base import BaseStorage
from app.utils.helpers import generate_id
from app.config import get_config

logger = logging.getLogger(__name__)


class OntologyStorage(BaseStorage):
    """本体存储"""

    def __init__(self, data_dir: str = None):
        """初始化本体存储，如果没有指定 data_dir 则使用配置中的默认值"""
        if data_dir is None:
            config = get_config()
            data_dir = str(config.data_dir)
        super().__init__(data_dir)

    def _ontology_path(self, project_id: str):
        """本体文件路径"""
        return self._get_project_dir(project_id) / "ontology" / "story_ontology.yaml"

    # ==================== 整体本体 ====================

    async def get_ontology(self, project_id: str) -> StoryOntology:
        """获取故事本体（不存在则创建空的）"""
        path = self._ontology_path(project_id)
        data = await self.read_yaml(path)

        if data:
            return StoryOntology(**data)

        # 创建空本体
        ontology = StoryOntology(project_id=project_id)
        return ontology

    async def save_ontology(self, project_id: str, ontology: StoryOntology) -> None:
        """保存故事本体"""
        path = self._ontology_path(project_id)
        ontology.version += 1
        await self.write_yaml(path, ontology.model_dump())
        logger.info(f"保存本体 v{ontology.version}: {project_id}")

    # ==================== 角色图操作 ====================

    async def add_character_node(
        self,
        project_id: str,
        name: str,
        status: CharacterStatus = CharacterStatus.ALIVE,
        location: str = "",
        goal: str = "",
        aliases: List[str] = None,
        groups: List[str] = None,
        chapter: str = ""
    ) -> CharacterNode:
        """添加或更新角色节点"""
        ontology = await self.get_ontology(project_id)

        node = CharacterNode(
            name=name,
            status=status,
            current_location=location,
            current_goal=goal,
            aliases=aliases or [],
            groups=groups or [],
            last_updated_chapter=chapter
        )

        ontology.characters.add_character(node)
        await self.save_ontology(project_id, ontology)

        return node

    async def update_character_status(
        self,
        project_id: str,
        name: str,
        status: CharacterStatus = None,
        location: str = None,
        goal: str = None,
        chapter: str = ""
    ) -> Optional[CharacterNode]:
        """更新角色状态"""
        ontology = await self.get_ontology(project_id)

        if name not in ontology.characters.nodes:
            logger.warning(f"角色不存在: {name}")
            return None

        node = ontology.characters.nodes[name]
        if status is not None:
            node.status = status
        if location is not None:
            node.current_location = location
        if goal is not None:
            node.current_goal = goal
        if chapter:
            node.last_updated_chapter = chapter

        await self.save_ontology(project_id, ontology)
        return node

    async def add_relationship(
        self,
        project_id: str,
        source: str,
        target: str,
        relation_type: RelationType,
        description: str = "",
        bidirectional: bool = False,
        chapter: str = ""
    ) -> Relationship:
        """添加角色关系"""
        ontology = await self.get_ontology(project_id)

        rel = Relationship(
            source=source,
            target=target,
            relation_type=relation_type,
            description=description,
            bidirectional=bidirectional,
            established_at=chapter
        )

        ontology.characters.add_relationship(rel)
        await self.save_ontology(project_id, ontology)

        return rel

    async def get_character_relationships(
        self,
        project_id: str,
        character: str
    ) -> List[Relationship]:
        """获取某角色的所有关系"""
        ontology = await self.get_ontology(project_id)
        return ontology.characters.get_relationships_for(character)

    # ==================== 世界观操作 ====================

    async def set_world_setting(
        self,
        project_id: str,
        setting: str = None,
        time_period: str = None
    ) -> WorldOntology:
        """设置世界背景"""
        ontology = await self.get_ontology(project_id)

        if setting is not None:
            ontology.world.setting = setting
        if time_period is not None:
            ontology.world.time_period = time_period

        await self.save_ontology(project_id, ontology)
        return ontology.world

    async def add_world_rule(
        self,
        project_id: str,
        rule: str,
        category: str = "general",
        immutable: bool = True,
        source: str = ""
    ) -> WorldRule:
        """添加世界规则"""
        ontology = await self.get_ontology(project_id)

        world_rule = WorldRule(
            id=generate_id("R"),
            rule=rule,
            category=category,
            immutable=immutable,
            source=source
        )

        ontology.world.add_rule(world_rule)
        await self.save_ontology(project_id, ontology)

        return world_rule

    async def add_faction(
        self,
        project_id: str,
        name: str,
        description: str = "",
        leader: str = "",
        members: List[str] = None,
        allies: List[str] = None,
        enemies: List[str] = None
    ) -> Faction:
        """添加势力/组织"""
        ontology = await self.get_ontology(project_id)

        faction = Faction(
            name=name,
            description=description,
            leader=leader,
            members=members or [],
            allies=allies or [],
            enemies=enemies or []
        )

        ontology.world.factions[name] = faction
        await self.save_ontology(project_id, ontology)

        return faction

    async def add_location(
        self,
        project_id: str,
        name: str,
        description: str = "",
        parent: str = ""
    ) -> Location:
        """添加地点"""
        ontology = await self.get_ontology(project_id)

        location = Location(
            name=name,
            description=description,
            parent=parent
        )

        ontology.world.locations[name] = location
        await self.save_ontology(project_id, ontology)

        return location

    # ==================== 时间线操作 ====================

    async def add_timeline_event(
        self,
        project_id: str,
        time: str,
        event: str,
        event_type: EventType = EventType.PLOT,
        participants: List[str] = None,
        location: str = "",
        source_chapter: str = "",
        importance: str = "normal",
        consequences: List[str] = None
    ) -> TimelineEvent:
        """添加时间线事件"""
        ontology = await self.get_ontology(project_id)

        timeline_event = TimelineEvent(
            id=generate_id("E"),
            time=time,
            event=event,
            event_type=event_type,
            participants=participants or [],
            location=location,
            source_chapter=source_chapter,
            importance=importance,
            consequences=consequences or []
        )

        ontology.timeline.add_event(timeline_event)

        # 更新当前时间
        if time:
            ontology.timeline.current_time = time

        await self.save_ontology(project_id, ontology)
        return timeline_event

    async def set_current_time(self, project_id: str, time: str) -> None:
        """设置当前故事时间"""
        ontology = await self.get_ontology(project_id)
        ontology.timeline.current_time = time
        await self.save_ontology(project_id, ontology)

    # ==================== 上下文获取 ====================

    async def get_writing_context(
        self,
        project_id: str,
        characters: List[str] = None,
        token_budget: int = 3000
    ) -> str:
        """获取写作用的紧凑上下文"""
        ontology = await self.get_ontology(project_id)
        return ontology.get_context_for_writing(characters, token_budget)

    async def get_review_context(
        self,
        project_id: str,
        characters: List[str] = None,
        token_budget: int = 5000
    ) -> str:
        """获取审稿用的上下文"""
        ontology = await self.get_ontology(project_id)
        return ontology.get_context_for_review(characters, token_budget)

    # ==================== 批量操作 ====================

    async def rebuild_from_chapter(
        self,
        project_id: str,
        chapter: str
    ) -> dict:
        """
        从某章节开始重建本体（删除该章节及之后的数据）
        返回删除的数量
        """
        ontology = await self.get_ontology(project_id)

        # 删除该章节及之后的时间线事件
        events_before = len(ontology.timeline.events)
        ontology.timeline.events = [
            e for e in ontology.timeline.events
            if e.source_chapter and e.source_chapter < chapter
        ]
        events_removed = events_before - len(ontology.timeline.events)

        # 删除该章节建立的关系
        rels_before = len(ontology.characters.relationships)
        ontology.characters.relationships = [
            r for r in ontology.characters.relationships
            if r.established_at and r.established_at < chapter
        ]
        rels_removed = rels_before - len(ontology.characters.relationships)

        # 重置角色状态到该章节之前
        # （这里简化处理，实际可能需要更复杂的逻辑）
        for node in ontology.characters.nodes.values():
            if node.last_updated_chapter and node.last_updated_chapter >= chapter:
                node.last_updated_chapter = ""
                node.current_location = ""
                node.current_goal = ""

        ontology.last_updated_chapter = ""
        await self.save_ontology(project_id, ontology)

        return {
            "events_removed": events_removed,
            "relationships_removed": rels_removed
        }

    async def clear_ontology(self, project_id: str) -> None:
        """清空本体（谨慎使用）"""
        path = self._ontology_path(project_id)
        if path.exists():
            path.unlink()
        logger.warning(f"已清空本体: {project_id}")
