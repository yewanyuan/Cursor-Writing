"""
写作会话 API
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core import Orchestrator
from app.api.websocket import broadcast

router = APIRouter()

# 调度器实例（每个项目一个）
_orchestrators: dict = {}

def get_orchestrator(project_id: str) -> Orchestrator:
    if project_id not in _orchestrators:
        orch = Orchestrator("../data")
        # 设置 WebSocket 广播回调
        async def on_progress(data):
            await broadcast(project_id, data)
        orch.on_progress = on_progress
        _orchestrators[project_id] = orch
    return _orchestrators[project_id]


class StartSessionRequest(BaseModel):
    project_id: str
    chapter: str
    chapter_title: str = ""
    chapter_goal: str = ""
    characters: List[str] = []
    target_words: int = 2000


class FeedbackRequest(BaseModel):
    action: str = "revise"  # revise / confirm
    content: Optional[str] = None


@router.post("/start")
async def start_session(req: StartSessionRequest):
    """开始写作会话"""
    orch = get_orchestrator(req.project_id)
    result = await orch.start_session(
        project_id=req.project_id,
        chapter=req.chapter,
        chapter_title=req.chapter_title,
        chapter_goal=req.chapter_goal,
        characters=req.characters,
        target_words=req.target_words
    )
    return result


@router.get("/status/{project_id}")
async def get_status(project_id: str):
    """获取会话状态"""
    orch = get_orchestrator(project_id)
    return orch.get_status()


@router.post("/feedback/{project_id}")
async def submit_feedback(project_id: str, req: FeedbackRequest):
    """提交反馈"""
    orch = get_orchestrator(project_id)
    result = await orch.submit_feedback(
        project_id=project_id,
        chapter=orch.current_chapter or "",
        feedback=req.content or "",
        action=req.action
    )
    return result


@router.post("/cancel/{project_id}")
async def cancel_session(project_id: str):
    """取消会话"""
    orch = get_orchestrator(project_id)
    orch.status = "idle"
    return {"success": True}
