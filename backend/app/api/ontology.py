"""
本体 API
提供故事本体的查询和管理接口
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage.ontology import OntologyStorage
from app.models.ontology import (
    CharacterStatus,
    RelationType,
    EventType
)

router = APIRouter()
storage = OntologyStorage()


# ==================== 响应模型 ====================

class CharacterNodeResponse(BaseModel):
    name: str
    status: str
    current_location: str
    current_goal: str
    aliases: List[str]
    groups: List[str]
    last_updated_chapter: str


class RelationshipResponse(BaseModel):
    source: str
    target: str
    relation_type: str
    description: str
    bidirectional: bool
    established_at: str


class TimelineEventResponse(BaseModel):
    id: str
    time: str
    event: str
    event_type: str
    participants: List[str]
    location: str
    source_chapter: str
    importance: str


class WorldRuleResponse(BaseModel):
    id: str
    rule: str
    category: str
    immutable: bool
    source: str


class OntologyOverview(BaseModel):
    """本体概览"""
    project_id: str
    version: int
    last_updated_chapter: str
    character_count: int
    relationship_count: int
    event_count: int
    rule_count: int
    location_count: int
    faction_count: int


# ==================== API 端点 ====================

@router.get("/{project_id}/overview", response_model=OntologyOverview)
async def get_ontology_overview(project_id: str):
    """获取本体概览"""
    ontology = await storage.get_ontology(project_id)
    return OntologyOverview(
        project_id=ontology.project_id,
        version=ontology.version,
        last_updated_chapter=ontology.last_updated_chapter,
        character_count=len(ontology.characters.nodes),
        relationship_count=len(ontology.characters.relationships),
        event_count=len(ontology.timeline.events),
        rule_count=len(ontology.world.rules),
        location_count=len(ontology.world.locations),
        faction_count=len(ontology.world.factions)
    )


@router.get("/{project_id}/characters", response_model=List[CharacterNodeResponse])
async def list_characters(project_id: str):
    """获取所有角色节点"""
    ontology = await storage.get_ontology(project_id)
    return [
        CharacterNodeResponse(
            name=node.name,
            status=node.status.value,
            current_location=node.current_location,
            current_goal=node.current_goal,
            aliases=node.aliases,
            groups=node.groups,
            last_updated_chapter=node.last_updated_chapter
        )
        for node in ontology.characters.nodes.values()
    ]


@router.get("/{project_id}/characters/{name}", response_model=CharacterNodeResponse)
async def get_character(project_id: str, name: str):
    """获取单个角色详情"""
    ontology = await storage.get_ontology(project_id)
    if name not in ontology.characters.nodes:
        raise HTTPException(status_code=404, detail="角色不存在")

    node = ontology.characters.nodes[name]
    return CharacterNodeResponse(
        name=node.name,
        status=node.status.value,
        current_location=node.current_location,
        current_goal=node.current_goal,
        aliases=node.aliases,
        groups=node.groups,
        last_updated_chapter=node.last_updated_chapter
    )


@router.get("/{project_id}/relationships", response_model=List[RelationshipResponse])
async def list_relationships(project_id: str, character: Optional[str] = None):
    """获取关系列表（可按角色筛选）"""
    ontology = await storage.get_ontology(project_id)

    if character:
        relationships = ontology.characters.get_relationships_for(character)
    else:
        relationships = ontology.characters.relationships

    return [
        RelationshipResponse(
            source=rel.source,
            target=rel.target,
            relation_type=rel.relation_type.value,
            description=rel.description,
            bidirectional=rel.bidirectional,
            established_at=rel.established_at
        )
        for rel in relationships
    ]


@router.get("/{project_id}/timeline", response_model=List[TimelineEventResponse])
async def list_timeline_events(
    project_id: str,
    character: Optional[str] = None,
    chapter: Optional[str] = None,
    limit: int = 50
):
    """获取时间线事件"""
    ontology = await storage.get_ontology(project_id)

    events = ontology.timeline.events

    if character:
        events = [e for e in events if character in e.participants]

    if chapter:
        events = [e for e in events if e.source_chapter == chapter]

    # 取最近的事件
    events = events[-limit:]

    return [
        TimelineEventResponse(
            id=e.id,
            time=e.time,
            event=e.event,
            event_type=e.event_type.value,
            participants=e.participants,
            location=e.location,
            source_chapter=e.source_chapter,
            importance=e.importance
        )
        for e in events
    ]


@router.get("/{project_id}/rules", response_model=List[WorldRuleResponse])
async def list_world_rules(project_id: str, immutable_only: bool = False):
    """获取世界规则"""
    ontology = await storage.get_ontology(project_id)

    rules = ontology.world.rules
    if immutable_only:
        rules = ontology.world.get_immutable_rules()

    return [
        WorldRuleResponse(
            id=rule.id,
            rule=rule.rule,
            category=rule.category,
            immutable=rule.immutable,
            source=rule.source
        )
        for rule in rules
    ]


@router.get("/{project_id}/context/writing")
async def get_writing_context(
    project_id: str,
    characters: Optional[str] = None,
    token_budget: int = 3000
):
    """获取写作上下文（紧凑格式）"""
    char_list = characters.split(",") if characters else None
    context = await storage.get_writing_context(
        project_id,
        characters=char_list,
        token_budget=token_budget
    )
    return {"context": context}


@router.get("/{project_id}/context/review")
async def get_review_context(
    project_id: str,
    characters: Optional[str] = None,
    token_budget: int = 5000
):
    """获取审稿上下文（详细格式）"""
    char_list = characters.split(",") if characters else None
    context = await storage.get_review_context(
        project_id,
        characters=char_list,
        token_budget=token_budget
    )
    return {"context": context}


@router.post("/{project_id}/rebuild/{from_chapter}")
async def rebuild_ontology(project_id: str, from_chapter: str):
    """从指定章节重建本体（删除该章节及之后的数据）"""
    result = await storage.rebuild_from_chapter(project_id, from_chapter)
    return {
        "success": True,
        "message": f"已重建本体，从章节 {from_chapter} 开始",
        **result
    }


@router.delete("/{project_id}")
async def clear_ontology(project_id: str):
    """清空本体（谨慎使用）"""
    await storage.clear_ontology(project_id)
    return {"success": True, "message": "本体已清空"}
