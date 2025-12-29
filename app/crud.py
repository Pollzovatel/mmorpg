from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

# === Игрок ===

def get_player_by_vk_id(db: Session, vk_id: int) -> Optional[models.Player]:
    return db.query(models.Player).filter(models.Player.vk_id == vk_id).first()


def create_player(db: Session, vk_id: int) -> models.Player:
    # Создаём игрока
    player = models.Player(
        vk_id=vk_id,
        name=f"Игрок {vk_id}",
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    
    # Создаём экипировку
    equipment = models.Equipment(
        player_id=player.id,
        weapon_name="Деревянный меч",
        weapon_icon="🗡️",
        weapon_attack=5,
    )
    db.add(equipment)
    
    # Добавляем стартовые предметы
    starter_items = [
        {"name": "Дерево", "icon": "🪵", "quantity": 20, "item_type": "material", "rarity": "common"},
        {"name": "Зелье HP", "icon": "❤️", "quantity": 5, "item_type": "potion", "rarity": "common"},
        {"name": "Еда", "icon": "🍖", "quantity": 10, "item_type": "food", "rarity": "common"},
    ]
    
    for item_data in starter_items:
        item = models.InventoryItem(player_id=player.id, **item_data)
        db.add(item)
    
    # Добавляем стартовый скин
    skin = models.OwnedSkin(player_id=player.id, skin_id="default")
    db.add(skin)
    
    db.commit()
    db.refresh(player)
    
    return player


def update_player_gold(db: Session, player_id: int, amount: int) -> models.Player:
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if player:
        player.gold += amount
        if player.gold < 0:
            player.gold = 0
        db.commit()
        db.refresh(player)
    return player


def update_player_crystals(db: Session, player_id: int, amount: int) -> models.Player:
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if player:
        player.crystals += amount
        if player.crystals < 0:
            player.crystals = 0
        db.commit()
        db.refresh(player)
    return player


# === Инвентарь ===

def get_inventory(db: Session, player_id: int) -> List[models.InventoryItem]:
    return db.query(models.InventoryItem).filter(
        models.InventoryItem.player_id == player_id
    ).all()


def add_inventory_item(db: Session, player_id: int, item: schemas.InventoryItemCreate) -> models.InventoryItem:
    # Проверяем, есть ли уже такой предмет
    existing = db.query(models.InventoryItem).filter(
        models.InventoryItem.player_id == player_id,
        models.InventoryItem.name == item.name
    ).first()
    
    if existing:
        existing.quantity += item.quantity
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_item = models.InventoryItem(player_id=player_id, **item.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item


def remove_inventory_item(db: Session, player_id: int, item_id: int, quantity: int = 1) -> bool:
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.player_id == player_id
    ).first()
    
    if not item:
        return False
    
    item.quantity -= quantity
    if item.quantity <= 0:
        db.delete(item)
    
    db.commit()
    return True


# === Биржа ===

def get_market_listings(db: Session, skip: int = 0, limit: int = 50) -> List[models.MarketListing]:
    return db.query(models.MarketListing).filter(
        models.MarketListing.is_active == True
    ).offset(skip).limit(limit).all()


def create_market_listing(db: Session, seller_id: int, listing: schemas.MarketListingCreate) -> models.MarketListing:
    db_listing = models.MarketListing(seller_id=seller_id, **listing.dict())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


def buy_market_listing(db: Session, buyer_id: int, listing_id: int) -> bool:
    listing = db.query(models.MarketListing).filter(
        models.MarketListing.id == listing_id,
        models.MarketListing.is_active == True
    ).first()
    
    if not listing:
        return False
    
    buyer = db.query(models.Player).filter(models.Player.id == buyer_id).first()
    seller = db.query(models.Player).filter(models.Player.id == listing.seller_id).first()
    
    total_price = listing.price * listing.quantity
    
    # Проверяем золото
    if buyer.gold < total_price:
        return False
    
    # Переводим золото (минус 5% комиссия)
    buyer.gold -= total_price
    seller.gold += int(total_price * 0.95)
    
    # Добавляем предмет покупателю
    add_inventory_item(db, buyer_id, schemas.InventoryItemCreate(
        name=listing.item_name,
        icon=listing.item_icon,
        quantity=listing.quantity,
        rarity=listing.item_rarity
    ))
    
    # Деактивируем лот
    listing.is_active = False
    
    db.commit()
    return True