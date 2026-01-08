"""
草稿存储：场景简报、草稿、审稿意见、摘要
"""

import re
from pathlib import Path
from typing import List, Optional

from app.models.draft import SceneBrief, Draft, Review, ChapterSummary
from app.storage.base import BaseStorage
from app.utils.helpers import count_words


class DraftStorage(BaseStorage):
    """草稿存储"""

    def _chapter_dir(self, project_id: str, chapter: str) -> Path:
        """获取章节目录"""
        return self._get_project_dir(project_id) / "drafts" / chapter

    # ========== 章节管理 ==========

    async def list_chapters(self, project_id: str) -> List[str]:
        """列出所有章节"""
        drafts_dir = self._get_project_dir(project_id) / "drafts"
        chapters = []
        if drafts_dir.exists():
            for d in drafts_dir.iterdir():
                if d.is_dir():
                    chapters.append(d.name)
        return self._sort_chapters(chapters)

    def _sort_chapters(self, chapters: List[str]) -> List[str]:
        """按章节号排序"""
        def sort_key(ch: str):
            match = re.match(r'ch(\d+)', ch)
            if match:
                return (1, int(match.group(1)))
            return (0, ch)  # 特殊章节排前面
        return sorted(chapters, key=sort_key)

    async def create_chapter(self, project_id: str, chapter: str) -> None:
        """创建章节目录"""
        chapter_dir = self._chapter_dir(project_id, chapter)
        chapter_dir.mkdir(parents=True, exist_ok=True)

    async def delete_chapter(self, project_id: str, chapter: str) -> bool:
        """删除章节"""
        import shutil
        chapter_dir = self._chapter_dir(project_id, chapter)
        if chapter_dir.exists():
            shutil.rmtree(chapter_dir)
            return True
        return False

    # ========== 场景简报 ==========

    async def get_brief(self, project_id: str, chapter: str) -> Optional[SceneBrief]:
        """获取场景简报"""
        path = self._chapter_dir(project_id, chapter) / "brief.yaml"
        data = await self.read_yaml(path)
        if data:
            return SceneBrief(**data)
        return None

    async def save_brief(self, project_id: str, brief: SceneBrief) -> None:
        """保存场景简报"""
        path = self._chapter_dir(project_id, brief.chapter) / "brief.yaml"
        await self.write_yaml(path, brief.model_dump())

    # ========== 草稿 ==========

    async def list_versions(self, project_id: str, chapter: str) -> List[str]:
        """列出草稿版本"""
        chapter_dir = self._chapter_dir(project_id, chapter)
        versions = []
        if chapter_dir.exists():
            for f in chapter_dir.glob("v*.md"):
                versions.append(f.stem)
        return sorted(versions)

    async def get_draft(self, project_id: str, chapter: str, version: str) -> Optional[Draft]:
        """获取草稿"""
        path = self._chapter_dir(project_id, chapter) / f"{version}.md"
        content = await self.read_text(path)
        if content is not None:
            return Draft(
                chapter=chapter,
                version=version,
                content=content,
                word_count=count_words(content)
            )
        return None

    async def save_draft(self, project_id: str, draft: Draft) -> Draft:
        """保存草稿"""
        draft.word_count = count_words(draft.content)
        path = self._chapter_dir(project_id, draft.chapter) / f"{draft.version}.md"
        await self.write_text(path, draft.content)
        return draft

    async def get_latest_draft(self, project_id: str, chapter: str) -> Optional[Draft]:
        """获取最新版本草稿"""
        versions = await self.list_versions(project_id, chapter)
        if versions:
            return await self.get_draft(project_id, chapter, versions[-1])
        return None

    async def get_next_version(self, project_id: str, chapter: str) -> str:
        """获取下一个版本号"""
        versions = await self.list_versions(project_id, chapter)
        if not versions:
            return "v1"
        last = versions[-1]
        num = int(last[1:])  # v1 -> 1
        return f"v{num + 1}"

    # ========== 审稿意见 ==========

    async def get_review(self, project_id: str, chapter: str) -> Optional[Review]:
        """获取审稿意见"""
        path = self._chapter_dir(project_id, chapter) / "review.yaml"
        data = await self.read_yaml(path)
        if data:
            return Review(**data)
        return None

    async def save_review(self, project_id: str, review: Review) -> None:
        """保存审稿意见"""
        path = self._chapter_dir(project_id, review.chapter) / "review.yaml"
        await self.write_yaml(path, review.model_dump())

    # ========== 成稿 ==========

    async def get_final(self, project_id: str, chapter: str) -> Optional[str]:
        """获取成稿"""
        path = self._chapter_dir(project_id, chapter) / "final.md"
        return await self.read_text(path)

    async def save_final(self, project_id: str, chapter: str, content: str) -> None:
        """保存成稿"""
        path = self._chapter_dir(project_id, chapter) / "final.md"
        await self.write_text(path, content)

    # ========== 章节摘要 ==========

    async def get_summary(self, project_id: str, chapter: str) -> Optional[ChapterSummary]:
        """获取章节摘要"""
        path = self._chapter_dir(project_id, chapter) / "summary.yaml"
        data = await self.read_yaml(path)
        if data:
            return ChapterSummary(**data)
        return None

    async def save_summary(self, project_id: str, summary: ChapterSummary) -> None:
        """保存章节摘要"""
        path = self._chapter_dir(project_id, summary.chapter) / "summary.yaml"
        await self.write_yaml(path, summary.model_dump())

    async def get_previous_summaries(self, project_id: str, current_chapter: str, limit: int = 5) -> List[ChapterSummary]:
        """获取前文摘要（用于上下文）"""
        chapters = await self.list_chapters(project_id)
        summaries = []

        try:
            idx = chapters.index(current_chapter)
        except ValueError:
            idx = len(chapters)

        # 取当前章节之前的摘要
        prev_chapters = chapters[:idx]
        for ch in prev_chapters[-limit:]:
            summary = await self.get_summary(project_id, ch)
            if summary:
                summaries.append(summary)

        return summaries
