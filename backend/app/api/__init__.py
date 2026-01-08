"""
API 路由 (API Routes)
FastAPI 路由定义
"""

from fastapi import APIRouter

from .projects import router as projects_router
from .cards import router as cards_router
from .drafts import router as drafts_router
from .session import router as session_router
from .websocket import router as websocket_router

# 汇总所有路由
api_router = APIRouter()
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(cards_router, prefix="/projects/{project_id}/cards", tags=["cards"])
api_router.include_router(drafts_router, prefix="/projects/{project_id}/drafts", tags=["drafts"])
api_router.include_router(session_router, prefix="/projects/{project_id}/session", tags=["session"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])

__all__ = ["api_router"]
