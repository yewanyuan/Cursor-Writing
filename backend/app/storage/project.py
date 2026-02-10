"""
项目存储
"""

import shutil
from pathlib import Path
from typing import List, Optional

from app.models.project import Project, ProjectCreate, ProjectUpdate
from app.storage.base import BaseStorage
from app.utils.helpers import sanitize_filename


class ProjectStorage(BaseStorage):
    """项目存储"""

    async def list_projects(self) -> List[Project]:
        """列出所有项目"""
        projects = []
        if not self.data_dir.exists():
            return projects

        for d in self.data_dir.iterdir():
            if d.is_dir():
                project = await self.get_project(d.name)
                if project:
                    projects.append(project)

        return sorted(projects, key=lambda p: p.updated_at, reverse=True)

    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        path = self._get_project_dir(project_id) / "project.yaml"
        data = await self.read_yaml(path)
        if data:
            return Project(**data)
        return None

    async def create_project(self, data: ProjectCreate) -> Project:
        """创建项目"""
        project_id = sanitize_filename(data.name)
        project_dir = self._get_project_dir(project_id)

        # 检查是否已存在
        if project_dir.exists():
            # 加后缀区分
            i = 1
            while (self.data_dir / f"{project_id}_{i}").exists():
                i += 1
            project_id = f"{project_id}_{i}"
            project_dir = self._get_project_dir(project_id)

        # 创建目录结构
        project_dir.mkdir(parents=True)
        (project_dir / "cards" / "characters").mkdir(parents=True)
        (project_dir / "cards" / "world").mkdir(parents=True)
        (project_dir / "canon").mkdir(parents=True)
        (project_dir / "drafts").mkdir(parents=True)

        # 保存项目信息
        project = Project(id=project_id, **data.model_dump())
        await self.save_project(project)

        # 创建默认文风卡和规则卡
        await self._create_default_cards(project_id)

        return project

    async def save_project(self, project: Project) -> None:
        """保存项目"""
        from datetime import datetime
        project.updated_at = datetime.now()
        path = self._get_project_dir(project.id) / "project.yaml"
        await self.write_yaml(path, project.model_dump())

    async def update_project(self, project_id: str, data: ProjectUpdate) -> Optional[Project]:
        """更新项目信息"""
        project = await self.get_project(project_id)
        if not project:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(project, key, value)

        await self.save_project(project)
        return project

    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        project_dir = self._get_project_dir(project_id)
        if project_dir.exists():
            shutil.rmtree(project_dir)
            return True
        return False

    async def _create_default_cards(self, project_id: str) -> None:
        """创建默认的文风卡和规则卡"""
        project_dir = self._get_project_dir(project_id)

        # 默认文风卡
        style_data = {
            "narrative_distance": "close",
            "pacing": "moderate",
            "sentence_style": "",
            "vocabulary": [],
            "taboo_words": [],
            "example_passages": []
        }
        await self.write_yaml(project_dir / "cards" / "style.yaml", style_data)

        # 默认规则卡
        rules_data = {
            "dos": [],
            "donts": [],
            "quality_standards": []
        }
        await self.write_yaml(project_dir / "cards" / "rules.yaml", rules_data)
