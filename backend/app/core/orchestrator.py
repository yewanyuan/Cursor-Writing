"""
调度器
协调多 Agent 完成写作流程
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable

from app.storage import ProjectStorage, CardStorage, CanonStorage, DraftStorage
from app.agents import ArchivistAgent, WriterAgent, ReviewerAgent, EditorAgent
from app.core.context import ContextSelector
from app.core.budgeter import get_budgeter

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """会话状态"""
    IDLE = "idle"
    BRIEFING = "briefing"       # 生成场景简报
    WRITING = "writing"         # 撰写草稿
    REVIEWING = "reviewing"     # 审核
    EDITING = "editing"         # 修订
    WAITING = "waiting"         # 等待用户反馈
    COMPLETED = "completed"
    ERROR = "error"


class Orchestrator:
    """调度器"""

    # 质量阈值配置
    QUALITY_THRESHOLD = 0.7     # 低于此分数需要重写
    MAX_REWRITE_ITERATIONS = 2  # 最大重写次数

    def __init__(self, data_dir: str = "../data"):
        # 存储
        self.projects = ProjectStorage(data_dir)
        self.cards = CardStorage(data_dir)
        self.canon = CanonStorage(data_dir)
        self.drafts = DraftStorage(data_dir)

        # Agents
        self.archivist = ArchivistAgent(self.cards, self.canon, self.drafts)
        self.writer = WriterAgent(self.cards, self.canon, self.drafts)
        self.reviewer = ReviewerAgent(self.cards, self.canon, self.drafts)
        self.editor = EditorAgent(self.cards, self.canon, self.drafts)

        # 上下文选择器
        self.context_selector = ContextSelector(self.cards, self.canon, self.drafts)

        # Token 预算管理器
        self.budgeter = get_budgeter()

        # 状态
        self.status = SessionStatus.IDLE
        self.current_project: Optional[str] = None
        self.current_chapter: Optional[str] = None
        self.iteration = 0
        self.rewrite_iteration = 0  # 重写迭代次数
        self.max_iterations = 5

        # 进度回调
        self.on_progress: Optional[Callable[[Dict], Awaitable[None]]] = None

    async def _notify(self, message: str):
        """通知进度"""
        if self.on_progress:
            await self.on_progress({
                "status": self.status.value,
                "message": message,
                "project": self.current_project,
                "chapter": self.current_chapter,
                "iteration": self.iteration,
                "rewrite_iteration": self.rewrite_iteration
            })

    async def start_session(
        self,
        project_id: str,
        chapter: str,
        chapter_title: str = "",
        chapter_goal: str = "",
        characters: list = None,
        target_words: int = 2000
    ) -> Dict[str, Any]:
        """
        开始写作会话

        完整流程：资料员 → 撰稿人 ↔ 审稿人 (循环) → 编辑
        """
        self.current_project = project_id
        self.current_chapter = chapter
        self.iteration = 0
        self.rewrite_iteration = 0

        try:
            # 确保章节目录存在
            await self.drafts.create_chapter(project_id, chapter)

            # 1. 资料员生成场景简报
            self.status = SessionStatus.BRIEFING
            await self._notify("资料员正在整理信息...")

            brief_result = await self.archivist.run(
                project_id, chapter,
                chapter_title=chapter_title,
                chapter_goal=chapter_goal,
                characters=characters or []
            )

            if not brief_result.get("success"):
                return await self._error("场景简报生成失败")

            # 2. Writer-Reviewer 质量循环
            write_result = None
            review_result = None

            for rewrite_i in range(self.MAX_REWRITE_ITERATIONS + 1):
                self.rewrite_iteration = rewrite_i

                # 2a. 撰稿人生成草稿
                self.status = SessionStatus.WRITING
                if rewrite_i == 0:
                    await self._notify("撰稿人正在撰写草稿...")
                else:
                    await self._notify(f"撰稿人根据审稿意见重写草稿（第 {rewrite_i} 次）...")

                # 如果是重写，传入上次的审稿意见
                writer_kwargs = {
                    "chapter_goal": chapter_goal,
                    "target_words": target_words
                }
                if review_result and rewrite_i > 0:
                    review = review_result.get("review")
                    if review:
                        writer_kwargs["review_feedback"] = review.summary

                write_result = await self.writer.run(
                    project_id, chapter,
                    **writer_kwargs
                )

                if not write_result.get("success"):
                    return await self._error("草稿生成失败")

                # 2b. 审稿人审核
                self.status = SessionStatus.REVIEWING
                await self._notify("审稿人正在审核...")

                review_result = await self.reviewer.run(project_id, chapter)

                if not review_result.get("success"):
                    # 审核失败不阻塞流程
                    logger.warning("审核失败，跳过质量检查")
                    break

                # 2c. 检查质量评分
                review = review_result.get("review")
                score = review.overall_score if review else 0.8

                logger.info(f"草稿质量评分: {score:.2f} (阈值: {self.QUALITY_THRESHOLD})")

                if score >= self.QUALITY_THRESHOLD:
                    # 质量达标，退出循环
                    await self._notify(f"草稿质量达标（评分 {score:.2f}）")
                    break
                elif rewrite_i < self.MAX_REWRITE_ITERATIONS:
                    # 质量不达标，继续循环重写
                    await self._notify(f"草稿质量不达标（评分 {score:.2f}），准备重写...")
                else:
                    # 达到最大重写次数
                    await self._notify(f"已达最大重写次数，当前评分 {score:.2f}")

            # 3. 编辑修订
            self.status = SessionStatus.EDITING
            await self._notify("编辑正在修订...")

            edit_result = await self.editor.run(project_id, chapter)

            # 4. 等待用户反馈
            self.status = SessionStatus.WAITING
            await self._notify("等待确认")

            return {
                "success": True,
                "status": self.status.value,
                "brief": brief_result.get("brief"),
                "draft": edit_result.get("draft"),
                "review": review_result.get("review") if review_result else None,
                "version": edit_result.get("version"),
                "quality_score": review_result.get("review").overall_score if review_result and review_result.get("review") else None,
                "rewrite_count": self.rewrite_iteration
            }

        except Exception as e:
            logger.exception("会话异常")
            return await self._error(str(e))

    async def submit_feedback(
        self,
        project_id: str,
        chapter: str,
        feedback: str = "",
        action: str = "revise"  # revise / confirm
    ) -> Dict[str, Any]:
        """处理用户反馈"""
        self.current_project = project_id
        self.current_chapter = chapter

        if action == "confirm":
            return await self._finalize(project_id, chapter)

        # 继续修订
        self.iteration += 1
        if self.iteration >= self.max_iterations:
            return {
                "success": False,
                "error": "已达到最大修订次数",
                "message": "建议确认当前版本或手动编辑"
            }

        try:
            # 编辑根据反馈修订
            self.status = SessionStatus.EDITING
            await self._notify(f"根据反馈修订中（第 {self.iteration} 轮）...")

            edit_result = await self.editor.run(
                project_id, chapter,
                feedback=feedback
            )

            if not edit_result.get("success"):
                return await self._error("修订失败")

            self.status = SessionStatus.WAITING
            await self._notify("等待确认")

            return {
                "success": True,
                "status": self.status.value,
                "draft": edit_result.get("draft"),
                "version": edit_result.get("version"),
                "iteration": self.iteration
            }

        except Exception as e:
            logger.exception("反馈处理异常")
            return await self._error(str(e))

    async def _finalize(self, project_id: str, chapter: str) -> Dict[str, Any]:
        """确认并完成章节"""
        try:
            # 获取最新草稿
            draft = await self.drafts.get_latest_draft(project_id, chapter)
            if not draft:
                return await self._error("找不到草稿")

            # 保存为成稿
            await self.drafts.save_final(project_id, chapter, draft.content)

            # 并行执行：生成摘要 + 提取事实
            await self._notify("正在生成摘要和提取事实...")

            summary_task = self.archivist.generate_summary(project_id, chapter, draft.content)
            facts_task = self.archivist.extract_facts(project_id, chapter, draft.content)

            summary_result, facts_result = await asyncio.gather(summary_task, facts_task)

            # 自动保存提取的事实到 Canon 存储
            saved_counts = {"facts": 0, "timeline": 0, "states": 0}

            if facts_result.get("success"):
                # 保存事实
                for fact in facts_result.get("facts", []):
                    await self.canon.add_fact(project_id, fact)
                    saved_counts["facts"] += 1

                # 保存时间线事件
                for event in facts_result.get("timeline", []):
                    await self.canon.add_timeline_event(project_id, event)
                    saved_counts["timeline"] += 1

                # 保存角色状态
                for state in facts_result.get("states", []):
                    await self.canon.update_character_state(project_id, state)
                    saved_counts["states"] += 1

                logger.info(
                    f"自动提取并保存: {saved_counts['facts']} 个事实, "
                    f"{saved_counts['timeline']} 个时间线事件, "
                    f"{saved_counts['states']} 个角色状态"
                )

            self.status = SessionStatus.COMPLETED
            await self._notify("章节完成")

            return {
                "success": True,
                "status": self.status.value,
                "message": "章节已完成",
                "extracted": saved_counts
            }

        except Exception as e:
            logger.exception("完成章节异常")
            return await self._error(str(e))

    async def _error(self, message: str) -> Dict[str, Any]:
        """处理错误"""
        self.status = SessionStatus.ERROR
        await self._notify(f"错误: {message}")
        return {
            "success": False,
            "status": self.status.value,
            "error": message
        }

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "status": self.status.value,
            "project": self.current_project,
            "chapter": self.current_chapter,
            "iteration": self.iteration,
            "rewrite_iteration": self.rewrite_iteration
        }
