"""
卡片存储：角色、世界观、文风、规则
"""

from pathlib import Path
from typing import List, Optional

from app.models.card import CharacterCard, WorldCard, StyleCard, RulesCard
from app.storage.base import BaseStorage
from app.utils.helpers import sanitize_filename


class CardStorage(BaseStorage):
    """卡片存储"""

    def __init__(self, data_dir: str = None):
        """初始化卡片存储，如果没有指定 data_dir 则使用配置中的默认值"""
        if data_dir is None:
            from app.config import get_config
            config = get_config()
            data_dir = str(config.data_dir)
        super().__init__(data_dir)

    # ========== 角色卡 ==========

    async def list_characters(self, project_id: str) -> List[str]:
        """列出所有角色名"""
        char_dir = self._get_project_dir(project_id) / "cards" / "characters"
        names = []
        if char_dir.exists():
            for f in char_dir.glob("*.yaml"):
                names.append(f.stem)
        return sorted(names)

    async def get_character(self, project_id: str, name: str) -> Optional[CharacterCard]:
        """获取角色卡"""
        path = self._get_project_dir(project_id) / "cards" / "characters" / f"{sanitize_filename(name)}.yaml"
        data = await self.read_yaml(path)
        if data:
            return CharacterCard(**data)
        return None

    async def save_character(self, project_id: str, card: CharacterCard) -> None:
        """保存角色卡"""
        path = self._get_project_dir(project_id) / "cards" / "characters" / f"{sanitize_filename(card.name)}.yaml"
        await self.write_yaml(path, card.model_dump())

    async def delete_character(self, project_id: str, name: str) -> bool:
        """删除角色卡"""
        path = self._get_project_dir(project_id) / "cards" / "characters" / f"{sanitize_filename(name)}.yaml"
        return await self.delete(path)

    # ========== 世界观卡 ==========

    async def list_world_cards(self, project_id: str) -> List[str]:
        """列出所有世界观卡名"""
        world_dir = self._get_project_dir(project_id) / "cards" / "world"
        names = []
        if world_dir.exists():
            for f in world_dir.glob("*.yaml"):
                names.append(f.stem)
        return sorted(names)

    async def get_world_card(self, project_id: str, name: str) -> Optional[WorldCard]:
        """获取世界观卡"""
        path = self._get_project_dir(project_id) / "cards" / "world" / f"{sanitize_filename(name)}.yaml"
        data = await self.read_yaml(path)
        if data:
            return WorldCard(**data)
        return None

    async def save_world_card(self, project_id: str, card: WorldCard) -> None:
        """保存世界观卡"""
        path = self._get_project_dir(project_id) / "cards" / "world" / f"{sanitize_filename(card.name)}.yaml"
        await self.write_yaml(path, card.model_dump())

    async def delete_world_card(self, project_id: str, name: str) -> bool:
        """删除世界观卡"""
        path = self._get_project_dir(project_id) / "cards" / "world" / f"{sanitize_filename(name)}.yaml"
        return await self.delete(path)

    # ========== 文风卡 ==========

    async def get_style(self, project_id: str) -> Optional[StyleCard]:
        """获取文风卡"""
        path = self._get_project_dir(project_id) / "cards" / "style.yaml"
        data = await self.read_yaml(path)
        if data:
            return StyleCard(**data)
        return None

    async def save_style(self, project_id: str, card: StyleCard) -> None:
        """保存文风卡"""
        path = self._get_project_dir(project_id) / "cards" / "style.yaml"
        await self.write_yaml(path, card.model_dump())

    # ========== 规则卡 ==========

    async def get_rules(self, project_id: str) -> Optional[RulesCard]:
        """获取规则卡"""
        path = self._get_project_dir(project_id) / "cards" / "rules.yaml"
        data = await self.read_yaml(path)
        if data:
            return RulesCard(**data)
        return None

    async def save_rules(self, project_id: str, card: RulesCard) -> None:
        """保存规则卡"""
        path = self._get_project_dir(project_id) / "cards" / "rules.yaml"
        await self.write_yaml(path, card.model_dump())
