"""
事实表模型：事实、时间线、角色状态
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class Fact(BaseModel):
    """事实条目"""
    id: str = ""                 # F20240101xxxx，自动生成
    statement: str               # 事实陈述
    source: str = ""             # 来源章节
    confidence: float = 1.0      # 置信度 0-1
    characters: List[str] = Field(default_factory=list)  # 相关角色
    importance: str = "normal"   # 重要性: critical / normal / minor


class TimelineEvent(BaseModel):
    """时间线事件"""
    id: str = ""                 # 自动生成
    time: str                    # 时间描述
    event: str                   # 事件描述
    participants: List[str] = Field(default_factory=list)
    location: str = ""
    source: str = ""


class CharacterState(BaseModel):
    """角色状态（某章节后的状态快照）"""
    character: str               # 角色名
    chapter: str                 # 截止章节
    location: str = ""
    emotional_state: str = ""
    goals: List[str] = Field(default_factory=list)
    inventory: List[str] = Field(default_factory=list)    # 持有物品
    injuries: List[str] = Field(default_factory=list)     # 伤势
    relationships: Dict[str, str] = Field(default_factory=dict)  # 与他人关系变化
