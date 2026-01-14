"""
草稿模型：场景简报、草稿、审稿意见、摘要
"""

from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SceneBrief(BaseModel):
    """场景简报（Archivist 生成）"""
    chapter: str
    title: str = ""
    goal: str                    # 本章目标
    characters: List[Dict] = Field(default_factory=list)   # 出场角色及状态
    timeline_context: Dict = Field(default_factory=dict)   # 时间线上下文
    world_constraints: List[str] = Field(default_factory=list)  # 世界观约束
    style_reminder: str = ""     # 文风提醒
    forbidden: List[str] = Field(default_factory=list)     # 禁止事项


class Draft(BaseModel):
    """草稿"""
    chapter: str
    version: str                 # v1, v2, ...
    content: str
    word_count: int = 0
    pending_confirmations: List[str] = Field(default_factory=list)  # [TO_CONFIRM] 标记
    created_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None  # 备注


class ReviewIssue(BaseModel):
    """审稿问题"""
    category: str                # consistency/style/plot/character
    problem: str
    suggestion: str = ""
    severity: str = "minor"      # minor/major/critical


class Review(BaseModel):
    """审稿意见（Reviewer 生成）"""
    chapter: str
    draft_version: str
    issues: List[ReviewIssue] = Field(default_factory=list)
    overall_score: float = 0.0   # 0-1
    summary: str = ""


class ChapterSummary(BaseModel):
    """章节摘要（Archivist 生成）"""
    chapter: str
    title: str = ""
    summary: str                 # 简要概述
    key_events: List[str] = Field(default_factory=list)
    character_changes: Dict[str, str] = Field(default_factory=dict)
