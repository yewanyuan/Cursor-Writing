"""
统计 API
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.statistics import StatisticsService

router = APIRouter()

_stats_service = None


def get_stats_service() -> StatisticsService:
    global _stats_service
    if _stats_service is None:
        _stats_service = StatisticsService("../data")
    return _stats_service


@router.get("/{project_id}")
async def get_project_stats(project_id: str):
    """获取项目完整统计"""
    service = get_stats_service()
    try:
        stats = await service.get_project_stats(project_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/overview")
async def get_overview(project_id: str):
    """获取概览统计"""
    service = get_stats_service()
    try:
        return await service.get_overview(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/trend")
async def get_word_trend(project_id: str, days: int = 30):
    """获取字数趋势"""
    service = get_stats_service()
    try:
        return await service.get_word_trend(project_id, days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/progress")
async def get_chapter_progress(project_id: str):
    """获取章节进度"""
    service = get_stats_service()
    try:
        return await service.get_chapter_progress(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
