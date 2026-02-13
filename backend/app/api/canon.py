"""
事实表 API (Canon API)
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.canon import Fact, TimelineEvent, CharacterState
from app.storage import CanonStorage, DraftStorage
from app.agents.archivist import ArchivistAgent

router = APIRouter()

_storage = None
_draft_storage = None
_archivist = None

def get_storage() -> CanonStorage:
    global _storage
    if _storage is None:
        _storage = CanonStorage("../data")
    return _storage

def get_draft_storage() -> DraftStorage:
    global _draft_storage
    if _draft_storage is None:
        _draft_storage = DraftStorage("../data")
    return _draft_storage

def get_archivist() -> ArchivistAgent:
    global _archivist
    if _archivist is None:
        _archivist = ArchivistAgent()
    return _archivist


class ExtractRequest(BaseModel):
    """AI 提取请求"""
    chapter: str
    content: Optional[str] = None  # 如果不提供，从草稿读取


class ExtractResponse(BaseModel):
    """AI 提取响应"""
    success: bool
    facts_count: int = 0
    timeline_count: int = 0
    states_count: int = 0
    message: str = ""


class BatchDeleteFactsRequest(BaseModel):
    """批量删除事实请求"""
    ids: List[str]


class BatchDeleteTimelineRequest(BaseModel):
    """批量删除时间线请求"""
    ids: List[str]


class BatchDeleteStatesRequest(BaseModel):
    """批量删除角色状态请求"""
    keys: List[dict]  # [{"character": "xxx", "chapter": "xxx"}, ...]


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    success: bool
    deleted_count: int
    message: str = ""


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


@router.post("/facts/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_facts(project_id: str, req: BatchDeleteFactsRequest):
    """批量删除事实"""
    facts = await get_storage().get_facts(project_id)
    ids_to_delete = set(req.ids)
    new_facts = [f for f in facts if f.id not in ids_to_delete]
    deleted_count = len(facts) - len(new_facts)

    if deleted_count == 0:
        return BatchDeleteResponse(
            success=True,
            deleted_count=0,
            message="没有找到要删除的事实"
        )

    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "facts.jsonl"
    if path.exists():
        path.unlink()
    for f in new_facts:
        await storage.append_jsonl(path, f.model_dump())

    return BatchDeleteResponse(
        success=True,
        deleted_count=deleted_count,
        message=f"成功删除 {deleted_count} 条事实"
    )


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


@router.post("/timeline/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_timeline(project_id: str, req: BatchDeleteTimelineRequest):
    """批量删除时间线事件"""
    events = await get_storage().get_timeline(project_id)
    ids_to_delete = set(req.ids)
    new_events = [e for e in events if e.id not in ids_to_delete]
    deleted_count = len(events) - len(new_events)

    if deleted_count == 0:
        return BatchDeleteResponse(
            success=True,
            deleted_count=0,
            message="没有找到要删除的事件"
        )

    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "timeline.jsonl"
    if path.exists():
        path.unlink()
    for e in new_events:
        await storage.append_jsonl(path, e.model_dump())

    return BatchDeleteResponse(
        success=True,
        deleted_count=deleted_count,
        message=f"成功删除 {deleted_count} 条时间线事件"
    )


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
    path = storage._get_project_dir(project_id) / "canon" / "states.jsonl"
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
    path = storage._get_project_dir(project_id) / "canon" / "states.jsonl"
    if path.exists():
        path.unlink()
    for s in new_states:
        await storage.append_jsonl(path, s.model_dump())
    return {"success": True}


@router.post("/states/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_states(project_id: str, req: BatchDeleteStatesRequest):
    """批量删除角色状态"""
    states = await get_storage().get_character_states(project_id)

    # 构建要删除的键集合
    keys_to_delete = set()
    for key in req.keys:
        if "character" in key and "chapter" in key:
            keys_to_delete.add((key["character"], key["chapter"]))

    new_states = [s for s in states if (s.character, s.chapter) not in keys_to_delete]
    deleted_count = len(states) - len(new_states)

    if deleted_count == 0:
        return BatchDeleteResponse(
            success=True,
            deleted_count=0,
            message="没有找到要删除的角色状态"
        )

    # 重写文件
    storage = get_storage()
    path = storage._get_project_dir(project_id) / "canon" / "states.jsonl"
    if path.exists():
        path.unlink()
    for s in new_states:
        await storage.append_jsonl(path, s.model_dump())

    return BatchDeleteResponse(
        success=True,
        deleted_count=deleted_count,
        message=f"成功删除 {deleted_count} 条角色状态"
    )


# ===== AI 提取 =====

@router.post("/extract", response_model=ExtractResponse)
async def extract_facts_from_chapter(project_id: str, req: ExtractRequest):
    """从章节内容中使用 AI 提取事实、时间线、角色状态"""
    content = req.content

    # 如果没有提供内容，尝试从草稿读取
    if not content:
        draft_storage = get_draft_storage()
        # 优先读取最终稿（get_final 返回的是字符串），其次读取最新草稿
        final_content = await draft_storage.get_final(project_id, req.chapter)
        if final_content:
            content = final_content  # get_final 直接返回字符串
        else:
            draft = await draft_storage.get_latest_draft(project_id, req.chapter)
            if draft:
                content = draft.content  # get_latest_draft 返回 Draft 对象

    if not content:
        raise HTTPException(400, f"章节 {req.chapter} 没有可用的内容")

    try:
        archivist = get_archivist()
        result = await archivist.extract_facts(project_id, req.chapter, content)

        if not result.get("success"):
            return ExtractResponse(
                success=False,
                message="AI 提取失败"
            )

        storage = get_storage()

        # 先删除该章节的旧数据（避免重复提取导致的重复问题）
        # 因为 AI 每次提取可能用不同措辞描述同一件事，精确匹配无法去重
        await storage.remove_facts_by_source(project_id, req.chapter)
        await storage.remove_timeline_by_source(project_id, req.chapter)
        await storage.remove_states_by_chapter(project_id, req.chapter)

        # 过滤出新的条目
        new_facts = result.get("facts", [])
        new_timeline = result.get("timeline", [])
        new_states = result.get("states", [])

        # 添加新提取的数据
        for fact in new_facts:
            await storage.add_fact(project_id, fact)

        for event in new_timeline:
            await storage.add_timeline_event(project_id, event)

        for state in new_states:
            await storage.update_character_state(project_id, state)

        # 直接使用提取的数量作为结果
        message = f"成功提取 {len(new_facts)} 条事实、{len(new_timeline)} 条时间线、{len(new_states)} 条角色状态"
        message += f"（已替换该章节的旧数据）"

        return ExtractResponse(
            success=True,
            facts_count=len(new_facts),
            timeline_count=len(new_timeline),
            states_count=len(new_states),
            message=message
        )

    except Exception as e:
        raise HTTPException(500, f"AI 提取失败: {str(e)}")

@router.delete("/clear")
async def clear_canon(project_id: str):
    """清空事实表"""
    await get_storage().clear_canon(project_id)
    return {"success": True}
