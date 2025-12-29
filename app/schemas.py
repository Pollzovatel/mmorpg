from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# === Игрок ===

class PlayerBase(BaseModel):
    name: str
    level: int = 1
    player_class: str = "⚔️ Воин"
    attack: int = 10
    defense: int = 5
    gold: int = 100
    crystals: int = 50

class PlayerCreate(BaseModel):
    vk_id: int

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    gold: Optional[int] = None
    crystals: Optional[int] = None
    current_skin: Optional[str] = None

class PlayerStats(BaseModel):
    attack: int
    defense: int
    gold: int

class PlayerEquipment(BaseModel):
    weapon: Optional[dict] = None
    armor: Optional[dict] = None
    accessory: Optional[dict] = None

class PlayerResponse(BaseModel):
    id: int
    vk_id: int
    name: str
    level: int
    player_class: str
    stats: PlayerStats
    crystals: int
    current_skin: str
    equipment: PlayerEquipment
    is_premium: bool
    
    class Config:
        from_attributes = True


# === Инвентарь ===

class InventoryItemBase(BaseModel):
    name: str
    icon: str
    quantity: int = 1
    item_type: str = "material"
    rarity: str = "common"

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: int
    
    class Config:
        from_attributes = True


# === Биржа ===

class MarketListingCreate(BaseModel):
    item_name: str
    item_icon: str
    item_rarity: str = "common"
    price: int
    quantity: int = 1

class MarketListingResponse(BaseModel):
    id: int
    seller_id: int
    seller_name: str
    item_name: str
    item_icon: str
    item_rarity: str
    price: int
    quantity: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# === VK Auth ===

class VKAuthParams(BaseModel):
    vk_user_id: int
    sign: str
    raw_params: str