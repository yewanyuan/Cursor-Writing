"""
事实表 API (Canon API)
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException

from app.models.canon import Fact, TimelineEvent, CharacterState
from app.storage import CanonStorage

router = APIRouter()

_storage = None

def get_storage() -> CanonStorage:
    global _storage
    if _storage is None:
        _storage = CanonStorage("../data")
    return _storage


# ===== 事实 (Facts) =====

@router.get("/facts", response_model=List[Fact])
async def list_facts(project_id: str):
    """获取所有事实"""
    return await get_storage().get_facts(project_id)


@router.get("/facts/{fact_id}", response_model=Fact)
async def get_fact(project_id: str, fact_id: str):
    """获取单个事实"""
    fact = await get_storage().find_fact(project_id, fact_id)
    if not fact:
        raise HTTPException(404, "事实不存在")
    return fact


@router.post("/facts", response_model=Fact)
async def create_fact(project_id: str, fact: Fact):
    """创建事实"""
    return await get_storage().add_fact(project_id, fact)


@router.put("/facts/{fact_id}", response_model=Fact)
async def update_fact(project_id: str, fact_id: str, fact: Fact):
    """更新事实"""
    facts = await get_storage().get_facts(project_id)
    found = False
    new_facts = []
    for f in facts:
        if f.id == fact_id:
            fact.id = fact_id  # 保持原ID
            new_facts.append(fact)
            found = True
        else:
            new_facts.append(f)
    if not found:
        raise HTTPException(404, "事实不存在")
    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "facts.jsonl"
    if path.exists():
        path.unlink()
    for f in new_facts:
        await storage.append_jsonl(path, f.model_dump())
    return fact


@router.delete("/facts/{fact_id}")
async def delete_fact(project_id: str, fact_id: str):
    """删除事实"""
    facts = await get_storage().get_facts(project_id)
    new_facts = [f for f in facts if f.id != fact_id]
    if len(new_facts) == len(facts):
        raise HTTPException(404, "事实不存在")
    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "facts.jsonl"
    if path.exists():
        path.unlink()
    for f in new_facts:
        await storage.append_jsonl(path, f.model_dump())
    return {"success": True}


# ===== 时间线 (Timeline) =====

@router.get("/timeline", response_model=List[TimelineEvent])
async def list_timeline(project_id: str):
    """获取时间线"""
    return await get_storage().get_timeline(project_id)


@router.post("/timeline", response_model=TimelineEvent)
async def create_timeline_event(project_id: str, event: TimelineEvent):
    """创建时间线事件"""
    return await get_storage().add_timeline_event(project_id, event)


@router.put("/timeline/{event_id}", response_model=TimelineEvent)
async def update_timeline_event(project_id: str, event_id: str, event: TimelineEvent):
    """更新时间线事件"""
    events = await get_storage().get_timeline(project_id)
    found = False
    new_events = []
    for e in events:
        if e.id == event_id:
            event.id = event_id  # 保持原ID
            new_events.append(event)
            found = True
        else:
            new_events.append(e)
    if not found:
        raise HTTPException(404, "事件不存在")
    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "timeline.jsonl"
    if path.exists():
        path.unlink()
    for e in new_events:
        await storage.append_jsonl(path, e.model_dump())
    return event


@router.delete("/timeline/{event_id}")
async def delete_timeline_event(project_id: str, event_id: str):
    """删除时间线事件"""
    events = await get_storage().get_timeline(project_id)
    new_events = [e for e in events if e.id != event_id]
    if len(new_events) == len(events):
        raise HTTPException(404, "事件不存在")
    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "timeline.jsonl"
    if path.exists():
        path.unlink()
    for e in new_events:
        await storage.append_jsonl(path, e.model_dump())
    return {"success": True}


# ===== 角色状态 (Character States) =====

@router.get("/states", response_model=List[CharacterState])
async def list_character_states(project_id: str):
    """获取所有角色状态"""
    return await get_storage().get_character_states(project_id)


@router.get("/states/{character}", response_model=CharacterState)
async def get_character_state(project_id: str, character: str):
    """获取角色最新状态"""
    state = await get_storage().get_character_state(project_id, character)
    if not state:
        raise HTTPException(404, "角色状态不存在")
    return state


@router.post("/states", response_model=CharacterState)
async def update_character_state(project_id: str, state: CharacterState):
    """更新角色状态（追加新状态）"""
    return await get_storage().update_character_state(project_id, state)


@router.put("/states/{character}/{chapter}", response_model=CharacterState)
async def edit_character_state(project_id: str, character: str, chapter: str, state: CharacterState):
    """编辑角色状态"""
    states = await get_storage().get_character_states(project_id)
    found = False
    new_states = []
    for s in states:
        if s.character == character and s.chapter == chapter:
            state.character = character
            state.chapter = chapter
            new_states.append(state)
            found = True
        else:
            new_states.append(s)
    if not found:
        raise HTTPException(404, "角色状态不存在")
    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "character_states.jsonl"
    if path.exists():
        path.unlink()
    for s in new_states:
        await storage.append_jsonl(path, s.model_dump())
    return state


@router.delete("/states/{character}/{chapter}")
async def delete_character_state(project_id: str, character: str, chapter: str):
    """删除角色状态"""
    states = await get_storage().get_character_states(project_id)
    new_states = [s for s in states if not (s.character == character and s.chapter == chapter)]
    if len(new_states) == len(states):
        raise HTTPException(404, "角色状态不存在")
    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "character_states.jsonl"
    if path.exists():
        path.unlink()
    for s in new_states:
        await storage.append_jsonl(path, s.model_dump())
    return {"success": True}


# ===== 批量操作 =====

@router.delete("/clear")
async def clear_canon(project_id: str):
    """清空事实表"""
    await get_storage().clear_canon(project_id)
    return {"success": True}
