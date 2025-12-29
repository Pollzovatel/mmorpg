
import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from . import models, schemas, crud
from .database import engine, get_db
from .vk_auth import verify_vk_signature, get_vk_user_id

# Создаём таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MMORPG Game API")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Проверка авторизации ===

async def verify_auth(x_vk_params: str = Header(None), db: Session = Depends(get_db)):
    """
    Проверяет подпись VK и возвращает игрока
    """
    is_debug = os.getenv("DEBUG", "true").lower() == "true"
    
    params = x_vk_params or "?vk_user_id=12345"
    
    if not is_debug and not verify_vk_signature(params):
        raise HTTPException(status_code=401, detail="Invalid VK signature")
    
    vk_id = get_vk_user_id(params)
    if not vk_id:
        vk_id = 12345
    
    player = crud.get_player_by_vk_id(db, vk_id)
    if not player:
        player = crud.create_player(db, vk_id)
    
    return player


# === Эндпоинты игрока ===

@app.get("/api/player", response_model=schemas.PlayerResponse)
async def get_player(
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Получить данные игрока"""
    equipment = player.equipment
    
    return schemas.PlayerResponse(
        id=player.id,
        vk_id=player.vk_id,
        name=player.name,
        level=player.level,
        player_class=player.player_class,
        stats=schemas.PlayerStats(
            attack=player.attack,
            defense=player.defense,
            gold=player.gold
        ),
        crystals=player.crystals,
        current_skin=player.current_skin,
        equipment=schemas.PlayerEquipment(
            weapon={"name": equipment.weapon_name, "icon": equipment.weapon_icon, "attack": equipment.weapon_attack} if equipment and equipment.weapon_name else None,
            armor={"name": equipment.armor_name, "icon": equipment.armor_icon, "defense": equipment.armor_defense} if equipment and equipment.armor_name else None,
            accessory=None
        ),
        is_premium=player.is_premium
    )


@app.post("/api/player/spend-gold")
async def spend_gold(
    data: dict,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Потратить золото"""
    amount = data.get("amount", 0)
    if player.gold < amount:
        raise HTTPException(status_code=400, detail="Not enough gold")
    
    player.gold -= amount
    db.commit()
    return {"success": True, "gold": player.gold}


@app.post("/api/player/add-gold")
async def add_gold(
    data: dict,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Добавить золото"""
    amount = data.get("amount", 0)
    player.gold += amount
    db.commit()
    return {"success": True, "gold": player.gold}


@app.post("/api/player/spend-crystals")
async def spend_crystals(
    data: dict,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Потратить кристаллы"""
    amount = data.get("amount", 0)
    if player.crystals < amount:
        raise HTTPException(status_code=400, detail="Not enough crystals")
    
    player.crystals -= amount
    db.commit()
    return {"success": True, "crystals": player.crystals}


@app.post("/api/player/add-crystals")
async def add_crystals(
    data: dict,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Добавить кристаллы"""
    amount = data.get("amount", 0)
    player.crystals += amount
    db.commit()
    return {"success": True, "crystals": player.crystals}


@app.post("/api/player/buy-skin")
async def buy_skin(
    data: dict,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Купить скин"""
    skin_id = data.get("skin_id")
    price = data.get("price", 0)
    
    if player.crystals < price:
        raise HTTPException(status_code=400, detail="Not enough crystals")
    
    player.crystals -= price
    player.current_skin = skin_id
    
    owned = models.OwnedSkin(player_id=player.id, skin_id=skin_id)
    db.add(owned)
    db.commit()
    
    return {"success": True, "skin_id": skin_id}


# === Эндпоинты инвентаря ===

@app.get("/api/inventory", response_model=List[schemas.InventoryItemResponse])
async def get_inventory(
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Получить инвентарь"""
    return crud.get_inventory(db, player.id)


@app.post("/api/inventory/use/{item_id}")
async def use_item(
    item_id: int,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Использовать предмет"""
    success = crud.remove_inventory_item(db, player.id, item_id, 1)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True}


@app.post("/api/inventory/add")
async def add_item(
    data: dict,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Добавить предмет в инвентарь"""
    item = schemas.InventoryItemCreate(
        name=data.get("name"),
        icon=data.get("icon"),
        quantity=data.get("quantity", 1),
        item_type=data.get("type", "material"),
        rarity=data.get("rarity", "common")
    )
    db_item = crud.add_inventory_item(db, player.id, item)
    return {"success": True, "item_id": db_item.id}


@app.post("/api/inventory/remove/{item_id}")
async def remove_item(
    item_id: int,
    data: dict,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Удалить предмет из инвентаря"""
    quantity = data.get("quantity", 1)
    success = crud.remove_inventory_item(db, player.id, item_id, quantity)
    
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"success": True}


# === Эндпоинты биржи ===

@app.get("/api/market")
async def get_market_listings(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Получить лоты на бирже"""
    listings = crud.get_market_listings(db, skip, limit)
    
    result = []
    for listing in listings:
        result.append({
            "id": listing.id,
            "seller_id": listing.seller_id,
            "seller_name": listing.seller.name,
            "item_name": listing.item_name,
            "item_icon": listing.item_icon,
            "item_rarity": listing.item_rarity,
            "price": listing.price,
            "quantity": listing.quantity,
            "created_at": listing.created_at.isoformat()
        })
    
    return result


@app.post("/api/market/sell")
async def create_listing(
    data: dict,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Выставить предмет на продажу"""
    listing = schemas.MarketListingCreate(
        item_name=data.get("item_name"),
        item_icon=data.get("item_icon"),
        item_rarity=data.get("item_rarity", "common"),
        price=data.get("price"),
        quantity=data.get("quantity", 1)
    )
    
    # Проверяем наличие предмета
    inventory = crud.get_inventory(db, player.id)
    item = next((i for i in inventory if i.name == listing.item_name and i.quantity >= listing.quantity), None)
    
    if not item:
        raise HTTPException(status_code=400, detail="Not enough items")
    
    # Убираем из инвентаря
    crud.remove_inventory_item(db, player.id, item.id, listing.quantity)
    
    # Создаём лот
    new_listing = crud.create_market_listing(db, player.id, listing)
    
    return {"success": True, "listing_id": new_listing.id}


@app.post("/api/market/buy/{listing_id}")
async def buy_listing(
    listing_id: int,
    player: models.Player = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Купить лот"""
    success = crud.buy_market_listing(db, player.id, listing_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Cannot buy this listing")
    
    return {"success": True}


# === Запуск ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)