"""
统计服务
提供项目写作统计数据：字数趋势、章节进度、创作时间分析
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

from app.storage import ProjectStorage, DraftStorage
from app.utils.helpers import count_words


@dataclass
class ChapterStats:
    """章节统计"""
    chapter: str
    word_count: int
    version_count: int
    status: str  # draft / final
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class DailyStats:
    """每日统计"""
    date: str
    word_count: int
    chapter_count: int
    version_count: int


@dataclass
class ProjectStats:
    """项目统计"""
    project_id: str
    project_name: str
    total_words: int
    total_chapters: int
    completed_chapters: int  # 有成稿的章节
    draft_chapters: int      # 只有草稿的章节
    total_versions: int      # 所有版本数
    avg_words_per_chapter: int
    chapters: List[ChapterStats]
    daily_stats: List[DailyStats]
    writing_days: int        # 有创作的天数
    first_created: Optional[str]
    last_updated: Optional[str]


class StatisticsService:
    """统计服务"""

    def __init__(self, data_dir: str = "../data"):
        self.projects = ProjectStorage(data_dir)
        self.drafts = DraftStorage(data_dir)
        self.data_dir = Path(data_dir)

    async def get_project_stats(self, project_id: str) -> ProjectStats:
        """获取项目统计数据"""
        project = await self.projects.get_project(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        chapters = await self.drafts.list_chapters(project_id)

        chapter_stats_list = []
        daily_word_counts: Dict[str, Dict] = defaultdict(lambda: {
            "word_count": 0,
            "chapter_count": 0,
            "version_count": 0
        })

        total_words = 0
        total_versions = 0
        completed_chapters = 0
        all_dates = []

        for chapter in chapters:
            # 获取版本列表
            versions = await self.drafts.list_versions(project_id, chapter)
            version_count = len(versions)
            total_versions += version_count

            # 检查是否有成稿
            final_content = await self.drafts.get_final(project_id, chapter)
            has_final = final_content is not None

            if has_final:
                completed_chapters += 1
                word_count = count_words(final_content)
                status = "final"
            else:
                # 使用最新草稿
                draft = await self.drafts.get_latest_draft(project_id, chapter)
                word_count = draft.word_count if draft else 0
                status = "draft"

            total_words += word_count

            # 获取创建和更新时间
            created_at = None
            updated_at = None

            # 遍历所有版本获取时间信息
            for version in versions:
                draft = await self.drafts.get_draft(project_id, chapter, version)
                if draft and draft.created_at:
                    date_str = draft.created_at.strftime("%Y-%m-%d")
                    all_dates.append(draft.created_at)

                    # 记录每日统计
                    if version == versions[0]:  # 第一个版本
                        daily_word_counts[date_str]["chapter_count"] += 1
                    daily_word_counts[date_str]["version_count"] += 1

                    # 更新创建时间（取最早）
                    if created_at is None:
                        created_at = draft.created_at.isoformat()

                    # 更新时间（取最新）
                    updated_at = draft.created_at.isoformat()

            # 计算该章节对当天字数的贡献
            if updated_at:
                date_str = updated_at[:10]
                daily_word_counts[date_str]["word_count"] += word_count

            chapter_stats_list.append(ChapterStats(
                chapter=chapter,
                word_count=word_count,
                version_count=version_count,
                status=status,
                created_at=created_at,
                updated_at=updated_at
            ))

        # 构建每日统计
        daily_stats = []
        for date_str in sorted(daily_word_counts.keys()):
            data = daily_word_counts[date_str]
            daily_stats.append(DailyStats(
                date=date_str,
                word_count=data["word_count"],
                chapter_count=data["chapter_count"],
                version_count=data["version_count"]
            ))

        # 计算写作天数和时间范围
        writing_days = len(daily_word_counts)
        first_created = min(all_dates).isoformat() if all_dates else None
        last_updated = max(all_dates).isoformat() if all_dates else None

        # 平均每章字数
        avg_words = total_words // len(chapters) if chapters else 0

        return ProjectStats(
            project_id=project_id,
            project_name=project.name,
            total_words=total_words,
            total_chapters=len(chapters),
            completed_chapters=completed_chapters,
            draft_chapters=len(chapters) - completed_chapters,
            total_versions=total_versions,
            avg_words_per_chapter=avg_words,
            chapters=[asdict(cs) for cs in chapter_stats_list],
            daily_stats=[asdict(ds) for ds in daily_stats],
            writing_days=writing_days,
            first_created=first_created,
            last_updated=last_updated
        )

    async def get_word_trend(
        self,
        project_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取字数趋势（最近 N 天）

        返回累计字数变化
        """
        stats = await self.get_project_stats(project_id)

        # 生成日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)

        # 创建日期到字数的映射
        date_words = {}
        for ds in stats.daily_stats:
            date_words[ds["date"]] = ds["word_count"]

        # 计算累计字数
        trend = []
        cumulative = 0
        current_date = start_date

        # 先计算 start_date 之前的累计字数
        for ds in stats.daily_stats:
            if ds["date"] < start_date.strftime("%Y-%m-%d"):
                cumulative += ds["word_count"]

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            day_words = date_words.get(date_str, 0)
            cumulative += day_words

            trend.append({
                "date": date_str,
                "words": cumulative,
                "daily_words": day_words
            })

            current_date += timedelta(days=1)

        return trend

    async def get_chapter_progress(self, project_id: str) -> List[Dict[str, Any]]:
        """获取章节进度"""
        stats = await self.get_project_stats(project_id)

        progress = []
        for ch in stats.chapters:
            progress.append({
                "chapter": ch["chapter"],
                "word_count": ch["word_count"],
                "status": ch["status"],
                "version_count": ch["version_count"],
                "progress": 100 if ch["status"] == "final" else min(95, ch["version_count"] * 20)
            })

        return progress

    async def get_overview(self, project_id: str) -> Dict[str, Any]:
        """获取概览统计"""
        stats = await self.get_project_stats(project_id)

        return {
            "total_words": stats.total_words,
            "total_chapters": stats.total_chapters,
            "completed_chapters": stats.completed_chapters,
            "draft_chapters": stats.draft_chapters,
            "total_versions": stats.total_versions,
            "avg_words_per_chapter": stats.avg_words_per_chapter,
            "writing_days": stats.writing_days,
            "first_created": stats.first_created,
            "last_updated": stats.last_updated,
            "completion_rate": round(stats.completed_chapters / stats.total_chapters * 100, 1) if stats.total_chapters > 0 else 0
        }
