"""
卡片模型：角色、世界观、文风、规则
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class CharacterCard(BaseModel):
    """角色卡"""
    name: str
    identity: str = ""           # 身份
    appearance: str = ""         # 外貌
    personality: List[str] = Field(default_factory=list)  # 性格特点
    motivation: str = ""         # 动机
    speech_pattern: str = ""     # 说话风格
    relationships: List[Dict] = Field(default_factory=list)  # 人际关系
    boundaries: List[str] = Field(default_factory=list)      # 行为边界（不会做的事）
    arc: str = ""                # 成长弧线


class WorldCard(BaseModel):
    """世界观卡"""
    name: str
    category: str = "location"   # location/rule/magic/organization
    description: str = ""
    rules: List[str] = Field(default_factory=list)
    immutable: bool = False      # 是否不可变更


class StyleCard(BaseModel):
    """文风卡"""
    narrative_distance: str = "close"     # 叙事距离：close/medium/far
    pacing: str = "moderate"              # 节奏：fast/moderate/slow
    sentence_style: str = ""              # 句式偏好
    vocabulary: List[str] = Field(default_factory=list)  # 词汇约束
    taboo_words: List[str] = Field(default_factory=list) # 禁用词汇
    example_passages: List[str] = Field(default_factory=list)  # 范文片段


class RulesCard(BaseModel):
    """规则卡"""
    dos: List[str] = Field(default_factory=list)       # 必须遵守
    donts: List[str] = Field(default_factory=list)     # 禁止事项
    quality_standards: List[str] = Field(default_factory=list)  # 质量标准
