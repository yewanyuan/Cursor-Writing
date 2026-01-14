"""
调度器
协调多 Agent 完成写作流程
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable

from app.storage import ProjectStorage, CardStorage, CanonStorage, DraftStorage
from app.agents import ArchivistAgent, WriterAgent, ReviewerAgent, EditorAgent
from app.core.context import ContextSelector

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

        # 状态
        self.status = SessionStatus.IDLE
        self.current_project: Optional[str] = None
        self.current_chapter: Optional[str] = None
        self.iteration = 0
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
                "iteration": self.iteration
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

        完整流程：资料员 → 撰稿人 → 审稿人 → 编辑
        """
        self.current_project = project_id
        self.current_chapter = chapter
        self.iteration = 0

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

            # 2. 撰稿人生成草稿
            self.status = SessionStatus.WRITING
            await self._notify("撰稿人正在撰写草稿...")

            write_result = await self.writer.run(
                project_id, chapter,
                chapter_goal=chapter_goal,
                target_words=target_words
            )

            if not write_result.get("success"):
                return await self._error("草稿生成失败")

            # 3. 审稿人审核
            self.status = SessionStatus.REVIEWING
            await self._notify("审稿人正在审核...")

            review_result = await self.reviewer.run(project_id, chapter)

            # 4. 编辑修订
            self.status = SessionStatus.EDITING
            await self._notify("编辑正在修订...")

            edit_result = await self.editor.run(project_id, chapter)

            # 5. 等待用户反馈
            self.status = SessionStatus.WAITING
            await self._notify("等待确认")

            return {
                "success": True,
                "status": self.status.value,
                "brief": brief_result.get("brief"),
                "draft": edit_result.get("draft"),
                "review": review_result.get("review"),
                "version": edit_result.get("version")
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

            # 生成摘要
            await self._notify("正在生成章节摘要...")
            await self.archivist.generate_summary(project_id, chapter, draft.content)

            # 提取事实
            await self._notify("正在提取事实...")
            await self.archivist.extract_facts(project_id, chapter, draft.content)

            self.status = SessionStatus.COMPLETED
            await self._notify("章节完成")

            return {
                "success": True,
                "status": self.status.value,
                "message": "章节已完成"
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
            "iteration": self.iteration
        }
