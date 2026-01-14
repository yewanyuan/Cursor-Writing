"""
项目 API
"""

from typing import List
from fastapi import APIRouter, HTTPException

from app.models.project import Project, ProjectCreate
from app.storage import ProjectStorage

router = APIRouter()

# 存储实例（后续可改为依赖注入）
_storage = None

def get_storage() -> ProjectStorage:
    global _storage
    if _storage is None:
        _storage = ProjectStorage("../data")
    return _storage


@router.get("", response_model=List[Project])
async def list_projects():
    """获取项目列表"""
    storage = get_storage()
    return await storage.list_projects()


@router.post("", response_model=Project)
async def create_project(data: ProjectCreate):
    """创建项目"""
    storage = get_storage()
    return await storage.create_project(data)


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """获取项目详情"""
    storage = get_storage()
    project = await storage.get_project(project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    storage = get_storage()
    success = await storage.delete_project(project_id)
    if not success:
        raise HTTPException(404, "项目不存在")
    return {"success": True}
