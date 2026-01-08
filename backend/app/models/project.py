"""
项目模型
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Project(BaseModel):
    """项目"""
    id: str
    name: str
    description: str = ""
    author: str = ""
    genre: str = ""  # 类型：玄幻、言情、科幻等
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProjectCreate(BaseModel):
    """创建项目的请求体"""
    name: str
    description: str = ""
    author: str = ""
    genre: str = ""
