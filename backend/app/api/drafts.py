"""
草稿 API
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.draft import Draft, SceneBrief, Review, ChapterSummary
from app.storage import DraftStorage

router = APIRouter()

_storage = None

def get_storage() -> DraftStorage:
    global _storage
    if _storage is None:
        _storage = DraftStorage("../data")
    return _storage


class DraftCreate(BaseModel):
    chapter: str
    content: str
    word_count: int = 0
    status: str = "draft"
    notes: Optional[str] = None


class DraftResponse(BaseModel):
    project_id: str
    chapter: str
    version: int
    content: str
    word_count: int
    status: str
    created_at: str
    notes: Optional[str] = None


@router.get("", response_model=List[DraftResponse])
async def list_drafts(project_id: str):
    """获取草稿列表"""
    storage = get_storage()
    chapters = await storage.list_chapters(project_id)
    drafts = []

    for chapter in chapters:
        versions = await storage.list_versions(project_id, chapter)
        if versions:
            # 获取最新版本（list_versions 已按数字排序）
            latest = versions[-1]
            draft = await storage.get_draft(project_id, chapter, latest)
            if draft:
                drafts.append(DraftResponse(
                    project_id=project_id,
                    chapter=chapter,
                    version=int(latest.replace("v", "")) if latest.startswith("v") else 1,
                    content=draft.content,
                    word_count=len(draft.content),
                    status="draft",
                    created_at=draft.created_at.isoformat() if draft.created_at else "",
                    notes=draft.notes
                ))

    return drafts


@router.post("")
async def save_draft(project_id: str, data: DraftCreate):
    """保存草稿"""
    storage = get_storage()

    # 确保章节目录存在
    await storage.create_chapter(project_id, data.chapter)

    # 获取下一个版本号
    version = await storage.get_next_version(project_id, data.chapter)

    draft = Draft(
        chapter=data.chapter,
        version=version,
        content=data.content,
        notes=data.notes
    )
    await storage.save_draft(project_id, draft)

    return DraftResponse(
        project_id=project_id,
        chapter=data.chapter,
        version=int(version.replace("v", "")) if version.startswith("v") else 1,
        content=data.content,
        word_count=data.word_count or len(data.content),
        status=data.status,
        created_at="",
        notes=data.notes
    )


@router.get("/{chapter}")
async def get_draft(project_id: str, chapter: str, version: Optional[int] = None):
    """获取草稿"""
    storage = get_storage()

    if version:
        version_str = f"v{version}"
    else:
        # 获取最新版本（list_versions 已按数字排序）
        versions = await storage.list_versions(project_id, chapter)
        if not versions:
            raise HTTPException(404, "草稿不存在")
        version_str = versions[-1]

    draft = await storage.get_draft(project_id, chapter, version_str)
    if not draft:
        raise HTTPException(404, "草稿不存在")

    return DraftResponse(
        project_id=project_id,
        chapter=chapter,
        version=int(version_str.replace("v", "")) if version_str.startswith("v") else 1,
        content=draft.content,
        word_count=len(draft.content),
        status="draft",
        created_at=draft.created_at.isoformat() if draft.created_at else "",
        notes=draft.notes
    )


@router.get("/{chapter}/versions", response_model=List[int])
async def list_versions(project_id: str, chapter: str):
    """获取草稿版本列表"""
    versions = await get_storage().list_versions(project_id, chapter)
    return [int(v.replace("v", "")) for v in versions if v.startswith("v")]


@router.delete("/{chapter}")
async def delete_chapter(project_id: str, chapter: str):
    """删除章节"""
    success = await get_storage().delete_chapter(project_id, chapter)
    if not success:
        raise HTTPException(404, "章节不存在")
    return {"success": True}


@router.get("/{chapter}/brief")
async def get_brief(project_id: str, chapter: str):
    """获取场景简报"""
    brief = await get_storage().get_brief(project_id, chapter)
    if not brief:
        raise HTTPException(404, "场景简报不存在")
    return brief


@router.get("/{chapter}/review")
async def get_review(project_id: str, chapter: str):
    """获取审稿意见"""
    review = await get_storage().get_review(project_id, chapter)
    if not review:
        raise HTTPException(404, "审稿意见不存在")
    return review


@router.get("/{chapter}/final")
async def get_final(project_id: str, chapter: str):
    """获取成稿"""
    content = await get_storage().get_final(project_id, chapter)
    if content is None:
        raise HTTPException(404, "成稿不存在")
    return {"chapter": chapter, "content": content}


@router.get("/{chapter}/summary")
async def get_summary(project_id: str, chapter: str):
    """获取章节摘要"""
    summary = await get_storage().get_summary(project_id, chapter)
    if not summary:
        raise HTTPException(404, "摘要不存在")
    return summary
