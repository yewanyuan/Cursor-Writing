"""
本体提取服务
从章节内容自动提取结构化信息更新到本体
"""

import logging
from typing import List, Dict, Any, Optional

from app.llm.client import get_client
from app.storage.ontology import OntologyStorage
from app.models.ontology import (
    CharacterStatus,
    RelationType,
    EventType
)
from app.utils.helpers import split_content_by_paragraphs

logger = logging.getLogger(__name__)


class OntologyExtractor:
    """本体提取器"""

    def __init__(self, storage: OntologyStorage = None):
        self.storage = storage or OntologyStorage()
        self.llm = get_client()

    async def extract_and_update(
        self,
        project_id: str,
        chapter: str,
        content: str,
        characters: List[str] = None
    ) -> Dict[str, Any]:
        """
        从章节内容提取本体信息并更新

        Args:
            project_id: 项目ID
            chapter: 章节标识
            content: 章节内容
            characters: 已知出场角色

        Returns:
            提取结果统计
        """
        # 分段处理长文本
        chunks = split_content_by_paragraphs(content, chunk_size=4000, overlap=300)

        stats = {
            "characters_added": 0,
            "characters_updated": 0,
            "relationships_added": 0,
            "events_added": 0,
            "rules_added": 0,
            "locations_added": 0,
            "factions_added": 0
        }

        for i, chunk in enumerate(chunks):
            chunk_info = f"（第 {i + 1}/{len(chunks)} 部分）" if len(chunks) > 1 else ""

            # 提取本体信息
            extraction = await self._extract_from_chunk(
                chunk=chunk,
                chapter=chapter,
                chunk_info=chunk_info,
                known_characters=characters
            )

            # 更新角色
            for char_data in extraction.get("characters", []):
                try:
                    existing = await self.storage.get_ontology(project_id)
                    if char_data["name"] in existing.characters.nodes:
                        await self.storage.update_character_status(
                            project_id=project_id,
                            name=char_data["name"],
                            status=self._parse_status(char_data.get("status")),
                            location=char_data.get("location"),
                            goal=char_data.get("goal"),
                            chapter=chapter
                        )
                        stats["characters_updated"] += 1
                    else:
                        await self.storage.add_character_node(
                            project_id=project_id,
                            name=char_data["name"],
                            status=self._parse_status(char_data.get("status")),
                            location=char_data.get("location", ""),
                            goal=char_data.get("goal", ""),
                            aliases=char_data.get("aliases", []),
                            groups=char_data.get("groups", []),
                            chapter=chapter
                        )
                        stats["characters_added"] += 1
                except Exception as e:
                    logger.warning(f"更新角色失败 {char_data.get('name')}: {e}")

            # 更新关系
            for rel_data in extraction.get("relationships", []):
                try:
                    await self.storage.add_relationship(
                        project_id=project_id,
                        source=rel_data["source"],
                        target=rel_data["target"],
                        relation_type=self._parse_relation_type(rel_data.get("type")),
                        description=rel_data.get("description", ""),
                        bidirectional=rel_data.get("bidirectional", False),
                        chapter=chapter
                    )
                    stats["relationships_added"] += 1
                except Exception as e:
                    logger.warning(f"添加关系失败: {e}")

            # 更新时间线事件
            for event_data in extraction.get("events", []):
                try:
                    await self.storage.add_timeline_event(
                        project_id=project_id,
                        time=event_data.get("time", ""),
                        event=event_data["event"],
                        event_type=self._parse_event_type(event_data.get("type")),
                        participants=event_data.get("participants", []),
                        location=event_data.get("location", ""),
                        source_chapter=chapter,
                        importance=event_data.get("importance", "normal"),
                        consequences=event_data.get("consequences", [])
                    )
                    stats["events_added"] += 1
                except Exception as e:
                    logger.warning(f"添加事件失败: {e}")

            # 更新世界规则
            for rule_data in extraction.get("rules", []):
                try:
                    await self.storage.add_world_rule(
                        project_id=project_id,
                        rule=rule_data["rule"],
                        category=rule_data.get("category", "general"),
                        immutable=rule_data.get("immutable", False),
                        source=chapter
                    )
                    stats["rules_added"] += 1
                except Exception as e:
                    logger.warning(f"添加规则失败: {e}")

            # 更新地点
            for loc_data in extraction.get("locations", []):
                try:
                    await self.storage.add_location(
                        project_id=project_id,
                        name=loc_data["name"],
                        description=loc_data.get("description", ""),
                        parent=loc_data.get("parent", "")
                    )
                    stats["locations_added"] += 1
                except Exception as e:
                    logger.warning(f"添加地点失败: {e}")

            # 更新势力
            for faction_data in extraction.get("factions", []):
                try:
                    await self.storage.add_faction(
                        project_id=project_id,
                        name=faction_data["name"],
                        description=faction_data.get("description", ""),
                        leader=faction_data.get("leader", ""),
                        members=faction_data.get("members", []),
                        allies=faction_data.get("allies", []),
                        enemies=faction_data.get("enemies", [])
                    )
                    stats["factions_added"] += 1
                except Exception as e:
                    logger.warning(f"添加势力失败: {e}")

        # 更新本体最后更新章节
        ontology = await self.storage.get_ontology(project_id)
        ontology.last_updated_chapter = chapter
        await self.storage.save_ontology(project_id, ontology)

        logger.info(f"本体提取完成: {stats}")
        return stats

    async def _extract_from_chunk(
        self,
        chunk: str,
        chapter: str,
        chunk_info: str = "",
        known_characters: List[str] = None
    ) -> Dict[str, Any]:
        """从文本块提取本体信息"""

        known_chars_hint = ""
        if known_characters:
            known_chars_hint = f"\n已知出场角色：{', '.join(known_characters)}"

        prompt = f"""从以下章节内容中提取结构化的故事本体信息：

章节：{chapter}{chunk_info}
{known_chars_hint}

{chunk}

## 提取要求

请提取以下类型的信息（只提取明确出现的，不要推测）：

### 1. 角色信息
- 新出现的角色（包括别名）
- 角色状态变化（位置、目标、生死状态）
- 角色所属组织/阵营

### 2. 角色关系
- 新建立的关系（家庭、社会、情感）
- 关系变化（敌变友、分手、结盟等）

### 3. 重要事件
- 关键情节事件
- 角色状态变化事件
- 关系变化事件

### 4. 世界规则（如有新揭示）
- 魔法/能力体系规则
- 社会规则
- 物理规则

### 5. 地点（如有新出现）
- 地点名称和描述
- 上级地点（如城市属于哪个国家）

### 6. 势力/组织（如有新出现）
- 组织名称和描述
- 领导者、成员

## 输出格式（JSON）

```json
{{
  "characters": [
    {{
      "name": "角色名",
      "status": "alive/dead/missing/unknown",
      "location": "当前位置",
      "goal": "当前目标",
      "aliases": ["别名1"],
      "groups": ["所属组织"]
    }}
  ],
  "relationships": [
    {{
      "source": "角色A",
      "target": "角色B",
      "type": "friend/enemy/lover/family/mentor/ally/rival/other",
      "description": "关系描述",
      "bidirectional": true
    }}
  ],
  "events": [
    {{
      "time": "故事时间",
      "event": "事件描述",
      "type": "plot/character/world/relationship",
      "participants": ["参与者"],
      "location": "地点",
      "importance": "critical/normal/minor",
      "consequences": ["后果1"]
    }}
  ],
  "rules": [
    {{
      "rule": "规则描述",
      "category": "magic/technology/social/physical/general",
      "immutable": true
    }}
  ],
  "locations": [
    {{
      "name": "地点名",
      "description": "描述",
      "parent": "上级地点"
    }}
  ],
  "factions": [
    {{
      "name": "组织名",
      "description": "描述",
      "leader": "领导者",
      "members": ["成员"],
      "allies": ["盟友组织"],
      "enemies": ["敌对组织"]
    }}
  ]
}}
```

注意：
- 只返回 JSON，不要其他内容
- 没有相关信息的字段可以返回空数组
- 角色关系类型参考：parent/child/sibling/spouse/friend/enemy/rival/ally/mentor/student/colleague/subordinate/superior/lover/ex_lover/crush/admirer/acquaintance/other
- 重要性分级：critical（核心转折）、normal（一般重要）、minor（细节）"""

        try:
            result = await self.llm.chat([
                {"role": "user", "content": prompt}
            ], temperature=0.3)

            response_text = result.get("content", "")

            # 提取 JSON
            import json
            import re

            # 尝试从代码块中提取
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response_text

            # 清理可能的前后缀
            json_str = json_str.strip()
            if json_str.startswith("```"):
                json_str = re.sub(r'^```\w*\n?', '', json_str)
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            extraction = json.loads(json_str)
            return extraction

        except Exception as e:
            logger.error(f"本体提取失败: {e}")
            return {
                "characters": [],
                "relationships": [],
                "events": [],
                "rules": [],
                "locations": [],
                "factions": []
            }

    def _parse_status(self, status: Optional[str]) -> CharacterStatus:
        """解析角色状态"""
        if not status:
            return CharacterStatus.ALIVE

        status_map = {
            "alive": CharacterStatus.ALIVE,
            "dead": CharacterStatus.DEAD,
            "missing": CharacterStatus.MISSING,
            "unknown": CharacterStatus.UNKNOWN
        }
        return status_map.get(status.lower(), CharacterStatus.ALIVE)

    def _parse_relation_type(self, rel_type: Optional[str]) -> RelationType:
        """解析关系类型"""
        if not rel_type:
            return RelationType.OTHER

        type_map = {
            "parent": RelationType.PARENT,
            "child": RelationType.CHILD,
            "sibling": RelationType.SIBLING,
            "spouse": RelationType.SPOUSE,
            "friend": RelationType.FRIEND,
            "enemy": RelationType.ENEMY,
            "rival": RelationType.RIVAL,
            "ally": RelationType.ALLY,
            "mentor": RelationType.MENTOR,
            "student": RelationType.STUDENT,
            "colleague": RelationType.COLLEAGUE,
            "subordinate": RelationType.SUBORDINATE,
            "superior": RelationType.SUPERIOR,
            "lover": RelationType.LOVER,
            "ex_lover": RelationType.EX_LOVER,
            "crush": RelationType.CRUSH,
            "admirer": RelationType.ADMIRER,
            "acquaintance": RelationType.ACQUAINTANCE,
            "family": RelationType.PARENT,  # 简化处理
        }
        return type_map.get(rel_type.lower(), RelationType.OTHER)

    def _parse_event_type(self, event_type: Optional[str]) -> EventType:
        """解析事件类型"""
        if not event_type:
            return EventType.PLOT

        type_map = {
            "plot": EventType.PLOT,
            "character": EventType.CHARACTER,
            "world": EventType.WORLD,
            "relationship": EventType.RELATIONSHIP
        }
        return type_map.get(event_type.lower(), EventType.PLOT)


# 全局实例
_extractor: Optional[OntologyExtractor] = None


def get_extractor() -> OntologyExtractor:
    """获取全局提取器实例"""
    global _extractor
    if _extractor is None:
        _extractor = OntologyExtractor()
    return _extractor
