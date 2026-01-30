"""
API 路由 (API Routes)
FastAPI 路由定义
"""

from fastapi import APIRouter

from .projects import router as projects_router
from .cards import router as cards_router
from .drafts import router as drafts_router
from .canon import router as canon_router
from .session import router as session_router
from .settings import router as settings_router
from .websocket import router as websocket_router
from .export import router as export_router
from .statistics import router as statistics_router

# 汇总所有路由
api_router = APIRouter()
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(cards_router, prefix="/projects/{project_id}/cards", tags=["cards"])
api_router.include_router(drafts_router, prefix="/projects/{project_id}/drafts", tags=["drafts"])
api_router.include_router(canon_router, prefix="/projects/{project_id}/canon", tags=["canon"])
api_router.include_router(session_router, prefix="/session", tags=["session"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
api_router.include_router(statistics_router, prefix="/stats", tags=["statistics"])

__all__ = ["api_router"]
