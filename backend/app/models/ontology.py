"""
上下文本体模型
结构化存储小说世界的核心信息，用于高效的上下文管理
"""

from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum


# ==================== 枚举类型 ====================

class RelationType(str, Enum):
    """关系类型"""
    # 家庭关系
    PARENT = "parent"           # 父母
    CHILD = "child"             # 子女
    SIBLING = "sibling"         # 兄弟姐妹
    SPOUSE = "spouse"           # 配偶

    # 社会关系
    FRIEND = "friend"           # 朋友
    ENEMY = "enemy"             # 敌人
    RIVAL = "rival"             # 对手/竞争者
    ALLY = "ally"               # 盟友
    MENTOR = "mentor"           # 导师
    STUDENT = "student"         # 学生
    COLLEAGUE = "colleague"     # 同事
    SUBORDINATE = "subordinate" # 下属
    SUPERIOR = "superior"       # 上级

    # 情感关系
    LOVER = "lover"             # 恋人
    EX_LOVER = "ex_lover"       # 前任
    CRUSH = "crush"             # 暗恋
    ADMIRER = "admirer"         # 仰慕者

    # 其他
    ACQUAINTANCE = "acquaintance"  # 认识
    STRANGER = "stranger"          # 陌生人
    OTHER = "other"                # 其他


class CharacterStatus(str, Enum):
    """角色状态"""
    ALIVE = "alive"
    DEAD = "dead"
    MISSING = "missing"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    """事件类型"""
    PLOT = "plot"               # 情节事件
    CHARACTER = "character"     # 角色事件（状态变化）
    WORLD = "world"             # 世界事件（环境变化）
    RELATIONSHIP = "relationship"  # 关系变化


# ==================== 角色关系图 ====================

class Relationship(BaseModel):
    """角色关系"""
    source: str                          # 关系发起者
    target: str                          # 关系对象
    relation_type: RelationType = RelationType.OTHER
    description: str = ""                # 关系描述（如"暗恋多年"）
    bidirectional: bool = False          # 是否双向关系
    established_at: str = ""             # 建立章节
    ended_at: str = ""                   # 结束章节（如分手）

    def to_text(self) -> str:
        """转为文本描述"""
        if self.description:
            return f"{self.source} → {self.target}: {self.description}"
        return f"{self.source} → {self.target}: {self.relation_type.value}"


class CharacterNode(BaseModel):
    """角色节点（轻量级，用于关系图）"""
    name: str
    status: CharacterStatus = CharacterStatus.ALIVE
    current_location: str = ""
    current_goal: str = ""
    last_updated_chapter: str = ""

    # 快速索引
    aliases: List[str] = Field(default_factory=list)  # 别名/称呼
    groups: List[str] = Field(default_factory=list)   # 所属组织/阵营


class CharacterGraph(BaseModel):
    """角色关系图"""
    nodes: Dict[str, CharacterNode] = Field(default_factory=dict)
    relationships: List[Relationship] = Field(default_factory=list)

    # 索引（不存储，运行时构建）
    _outgoing_index: Dict[str, List[int]] = {}  # name -> [relationship_indices]
    _incoming_index: Dict[str, List[int]] = {}

    def add_character(self, node: CharacterNode) -> None:
        """添加角色"""
        self.nodes[node.name] = node
        # 添加别名索引
        for alias in node.aliases:
            if alias not in self.nodes:
                self.nodes[alias] = node

    def add_relationship(self, rel: Relationship) -> None:
        """添加关系"""
        self.relationships.append(rel)
        # 如果是双向关系，添加反向
        if rel.bidirectional:
            reverse = Relationship(
                source=rel.target,
                target=rel.source,
                relation_type=rel.relation_type,
                description=rel.description,
                bidirectional=True,
                established_at=rel.established_at,
                ended_at=rel.ended_at
            )
            self.relationships.append(reverse)

    def get_relationships_for(self, character: str) -> List[Relationship]:
        """获取某角色的所有关系"""
        return [r for r in self.relationships
                if r.source == character or r.target == character]

    def get_relationships_between(self, char1: str, char2: str) -> List[Relationship]:
        """获取两个角色之间的关系"""
        return [r for r in self.relationships
                if (r.source == char1 and r.target == char2) or
                   (r.source == char2 and r.target == char1)]

    def get_characters_by_group(self, group: str) -> List[str]:
        """获取某组织/阵营的所有角色"""
        return [name for name, node in self.nodes.items()
                if group in node.groups]

    def find_path(self, source: str, target: str, max_depth: int = 3) -> List[str]:
        """查找两个角色之间的关系链（BFS）"""
        if source not in self.nodes or target not in self.nodes:
            return []

        visited = {source}
        queue = [(source, [source])]

        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue

            for rel in self.relationships:
                next_char = None
                if rel.source == current and rel.target not in visited:
                    next_char = rel.target
                elif rel.target == current and rel.source not in visited:
                    next_char = rel.source

                if next_char:
                    new_path = path + [next_char]
                    if next_char == target:
                        return new_path
                    visited.add(next_char)
                    queue.append((next_char, new_path))

        return []

    def to_compact_text(self, characters: List[str] = None) -> str:
        """转为紧凑文本（用于 LLM 上下文）"""
        lines = []

        # 筛选相关角色
        if characters:
            relevant_chars = set(characters)
            # 添加与这些角色有直接关系的角色
            for rel in self.relationships:
                if rel.source in relevant_chars:
                    relevant_chars.add(rel.target)
                if rel.target in relevant_chars:
                    relevant_chars.add(rel.source)
        else:
            relevant_chars = set(self.nodes.keys())

        # 输出角色状态
        lines.append("[角色状态]")
        for name in relevant_chars:
            if name in self.nodes:
                node = self.nodes[name]
                status_str = f"{name}"
                if node.status != CharacterStatus.ALIVE:
                    status_str += f"({node.status.value})"
                if node.current_location:
                    status_str += f" @{node.current_location}"
                lines.append(status_str)

        # 输出关系
        lines.append("\n[角色关系]")
        seen_rels = set()
        for rel in self.relationships:
            if rel.source in relevant_chars or rel.target in relevant_chars:
                # 避免重复输出双向关系
                key = tuple(sorted([rel.source, rel.target])) + (rel.relation_type,)
                if key not in seen_rels:
                    lines.append(rel.to_text())
                    seen_rels.add(key)

        return "\n".join(lines)


# ==================== 世界观本体 ====================

class WorldRule(BaseModel):
    """世界规则"""
    id: str = ""
    rule: str                            # 规则描述
    category: str = "general"            # magic/technology/social/physical
    immutable: bool = True               # 是否不可违反
    source: str = ""                     # 来源章节

    def to_text(self) -> str:
        prefix = "[不可违反]" if self.immutable else ""
        return f"{prefix}{self.rule}"


class Location(BaseModel):
    """地点"""
    name: str
    description: str = ""
    parent: str = ""                     # 上级地点（如：城市 -> 国家）
    attributes: Dict[str, str] = Field(default_factory=dict)


class Faction(BaseModel):
    """势力/组织"""
    name: str
    description: str = ""
    leader: str = ""                     # 领导者
    members: List[str] = Field(default_factory=list)
    allies: List[str] = Field(default_factory=list)     # 友好势力
    enemies: List[str] = Field(default_factory=list)    # 敌对势力
    goals: List[str] = Field(default_factory=list)


class WorldOntology(BaseModel):
    """世界观本体"""
    setting: str = ""                    # 背景设定（一句话描述）
    time_period: str = ""                # 时代
    rules: List[WorldRule] = Field(default_factory=list)
    locations: Dict[str, Location] = Field(default_factory=dict)
    factions: Dict[str, Faction] = Field(default_factory=dict)

    # 特殊元素（如魔法体系、科技水平等）
    special_elements: Dict[str, str] = Field(default_factory=dict)

    def add_rule(self, rule: WorldRule) -> None:
        """添加规则"""
        self.rules.append(rule)

    def get_immutable_rules(self) -> List[WorldRule]:
        """获取不可违反的规则"""
        return [r for r in self.rules if r.immutable]

    def check_rule_violation(self, action: str) -> List[WorldRule]:
        """检查行为是否违反规则（简单关键词匹配，可扩展为语义匹配）"""
        violations = []
        action_lower = action.lower()
        for rule in self.rules:
            # 简单的否定词检测
            if "不能" in rule.rule or "禁止" in rule.rule or "不可" in rule.rule:
                # 提取关键词
                keywords = [w for w in rule.rule if len(w) > 1]
                if any(kw in action_lower for kw in keywords):
                    violations.append(rule)
        return violations

    def to_compact_text(self) -> str:
        """转为紧凑文本"""
        lines = []

        if self.setting:
            lines.append(f"[世界背景] {self.setting}")

        if self.time_period:
            lines.append(f"[时代] {self.time_period}")

        # 只输出不可违反的规则
        immutable_rules = self.get_immutable_rules()
        if immutable_rules:
            lines.append("\n[核心规则]")
            for rule in immutable_rules[:10]:  # 最多10条
                lines.append(f"- {rule.rule}")

        # 势力
        if self.factions:
            lines.append("\n[主要势力]")
            for name, faction in list(self.factions.items())[:5]:
                desc = f"{name}"
                if faction.leader:
                    desc += f"(领袖:{faction.leader})"
                lines.append(desc)

        return "\n".join(lines)


# ==================== 时间线 ====================

class TimelineEvent(BaseModel):
    """时间线事件"""
    id: str = ""
    time: str                            # 时间描述（故事内时间）
    event: str                           # 事件描述
    event_type: EventType = EventType.PLOT
    participants: List[str] = Field(default_factory=list)
    location: str = ""
    source_chapter: str = ""             # 来源章节
    importance: str = "normal"           # critical/normal/minor

    # 影响
    consequences: List[str] = Field(default_factory=list)

    def to_text(self) -> str:
        """转为文本"""
        parts = [f"[{self.time}]", self.event]
        if self.participants:
            parts.append(f"({', '.join(self.participants)})")
        return " ".join(parts)


class Timeline(BaseModel):
    """时间线"""
    events: List[TimelineEvent] = Field(default_factory=list)
    current_time: str = ""               # 当前故事时间

    # 索引
    _chapter_index: Dict[str, List[int]] = {}  # chapter -> [event_indices]
    _character_index: Dict[str, List[int]] = {}  # character -> [event_indices]

    def add_event(self, event: TimelineEvent) -> None:
        """添加事件"""
        self.events.append(event)

    def get_events_by_chapter(self, chapter: str) -> List[TimelineEvent]:
        """获取某章节的事件"""
        return [e for e in self.events if e.source_chapter == chapter]

    def get_events_for_character(self, character: str) -> List[TimelineEvent]:
        """获取某角色参与的事件"""
        return [e for e in self.events if character in e.participants]

    def get_recent_events(self, n: int = 10) -> List[TimelineEvent]:
        """获取最近的事件"""
        return self.events[-n:] if len(self.events) > n else self.events

    def get_critical_events(self) -> List[TimelineEvent]:
        """获取关键事件"""
        return [e for e in self.events if e.importance == "critical"]

    def to_compact_text(self, characters: List[str] = None, limit: int = 15) -> str:
        """转为紧凑文本"""
        lines = ["[时间线]"]

        # 筛选相关事件
        if characters:
            relevant_events = [
                e for e in self.events
                if any(c in e.participants for c in characters) or e.importance == "critical"
            ]
        else:
            relevant_events = self.events

        # 取最近的 + 关键的
        critical = [e for e in relevant_events if e.importance == "critical"]
        recent = relevant_events[-limit:]

        # 合并去重
        selected = list({e.id or e.event: e for e in critical + recent}.values())

        for event in selected[-limit:]:
            lines.append(event.to_text())

        if self.current_time:
            lines.append(f"\n[当前时间] {self.current_time}")

        return "\n".join(lines)


# ==================== 聚合的上下文本体 ====================

class StoryOntology(BaseModel):
    """故事本体（聚合所有结构化信息）"""
    project_id: str

    # 三大核心组件
    world: WorldOntology = Field(default_factory=WorldOntology)
    characters: CharacterGraph = Field(default_factory=CharacterGraph)
    timeline: Timeline = Field(default_factory=Timeline)

    # 元数据
    last_updated_chapter: str = ""
    version: int = 1

    def get_context_for_writing(
        self,
        chapter_characters: List[str] = None,
        token_budget: int = 3000
    ) -> str:
        """
        获取写作用的紧凑上下文

        优先级：
        1. 核心世界规则
        2. 相关角色关系
        3. 近期时间线
        """
        parts = []

        # 1. 世界观（约 500 tokens）
        world_text = self.world.to_compact_text()
        parts.append(world_text)

        # 2. 角色关系（约 1000 tokens）
        char_text = self.characters.to_compact_text(chapter_characters)
        parts.append(char_text)

        # 3. 时间线（约 1000 tokens）
        timeline_text = self.timeline.to_compact_text(chapter_characters)
        parts.append(timeline_text)

        return "\n\n".join(parts)

    def get_context_for_review(
        self,
        chapter_characters: List[str] = None,
        token_budget: int = 5000
    ) -> str:
        """
        获取审稿用的上下文（比写作更详细）
        """
        parts = []

        # 世界观（包含所有规则）
        parts.append("[世界观]")
        if self.world.setting:
            parts.append(f"背景: {self.world.setting}")
        for rule in self.world.rules[:20]:
            parts.append(f"- {rule.to_text()}")

        # 角色关系（更详细）
        parts.append("\n" + self.characters.to_compact_text(chapter_characters))

        # 时间线（更多事件）
        parts.append("\n" + self.timeline.to_compact_text(chapter_characters, limit=25))

        return "\n".join(parts)
