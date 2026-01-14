"""
卡片 API
"""

from typing import List
from fastapi import APIRouter, HTTPException

from app.models.card import CharacterCard, WorldCard, StyleCard, RulesCard
from app.storage import CardStorage

router = APIRouter()

_storage = None

def get_storage() -> CardStorage:
    global _storage
    if _storage is None:
        _storage = CardStorage("../data")
    return _storage


# ===== 角色卡 =====

@router.get("/characters", response_model=List[CharacterCard])
async def list_characters(project_id: str):
    """获取角色列表（完整信息）"""
    storage = get_storage()
    names = await storage.list_characters(project_id)
    cards = []
    for name in names:
        card = await storage.get_character(project_id, name)
        if card:
            cards.append(card)
    return cards


@router.get("/characters/{name}", response_model=CharacterCard)
async def get_character(project_id: str, name: str):
    """获取角色卡"""
    card = await get_storage().get_character(project_id, name)
    if not card:
        raise HTTPException(404, "角色不存在")
    return card


@router.post("/characters", response_model=CharacterCard)
async def create_character(project_id: str, card: CharacterCard):
    """创建角色卡"""
    await get_storage().save_character(project_id, card)
    return card


@router.put("/characters/{name}", response_model=CharacterCard)
async def update_character(project_id: str, name: str, card: CharacterCard):
    """更新角色卡"""
    # 如果改名，删除旧文件
    if card.name != name:
        await get_storage().delete_character(project_id, name)
    await get_storage().save_character(project_id, card)
    return card


@router.delete("/characters/{name}")
async def delete_character(project_id: str, name: str):
    """删除角色卡"""
    success = await get_storage().delete_character(project_id, name)
    if not success:
        raise HTTPException(404, "角色不存在")
    return {"success": True}


# ===== 世界观卡 =====

@router.get("/worlds", response_model=List[WorldCard])
async def list_world_cards(project_id: str):
    """获取世界观卡列表（完整信息）"""
    storage = get_storage()
    names = await storage.list_world_cards(project_id)
    cards = []
    for name in names:
        card = await storage.get_world_card(project_id, name)
        if card:
            cards.append(card)
    return cards


@router.get("/worlds/{name}", response_model=WorldCard)
async def get_world_card(project_id: str, name: str):
    """获取世界观卡"""
    card = await get_storage().get_world_card(project_id, name)
    if not card:
        raise HTTPException(404, "设定不存在")
    return card


@router.post("/worlds", response_model=WorldCard)
async def create_world_card(project_id: str, card: WorldCard):
    """创建世界观卡"""
    await get_storage().save_world_card(project_id, card)
    return card


@router.put("/worlds/{name}", response_model=WorldCard)
async def update_world_card(project_id: str, name: str, card: WorldCard):
    """更新世界观卡"""
    if card.name != name:
        await get_storage().delete_world_card(project_id, name)
    await get_storage().save_world_card(project_id, card)
    return card


@router.delete("/worlds/{name}")
async def delete_world_card(project_id: str, name: str):
    """删除世界观卡"""
    success = await get_storage().delete_world_card(project_id, name)
    if not success:
        raise HTTPException(404, "设定不存在")
    return {"success": True}


# ===== 文风卡 =====

@router.get("/style", response_model=StyleCard)
async def get_style(project_id: str):
    """获取文风卡"""
    card = await get_storage().get_style(project_id)
    if not card:
        # 返回默认空卡片
        return StyleCard()
    return card


@router.put("/style", response_model=StyleCard)
async def update_style(project_id: str, card: StyleCard):
    """更新文风卡"""
    await get_storage().save_style(project_id, card)
    return card


# ===== 规则卡 =====

@router.get("/rules", response_model=RulesCard)
async def get_rules(project_id: str):
    """获取规则卡"""
    card = await get_storage().get_rules(project_id)
    if not card:
        # 返回默认空卡片
        return RulesCard()
    return card


@router.put("/rules", response_model=RulesCard)
async def update_rules(project_id: str, card: RulesCard):
    """更新规则卡"""
    await get_storage().save_rules(project_id, card)
    return card
