from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    vk_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(100), default="Новый игрок")
    level = Column(Integer, default=1)
    player_class = Column(String(50), default="⚔️ Воин")
    
    # Статы
    attack = Column(Integer, default=10)
    defense = Column(Integer, default=5)
    gold = Column(Integer, default=100)
    crystals = Column(Integer, default=50)
    
    # Премиум
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    current_skin = Column(String(50), default="default")
    
    # Время
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Связи
    inventory = relationship("InventoryItem", back_populates="player")
    equipment = relationship("Equipment", back_populates="player", uselist=False)
    owned_skins = relationship("OwnedSkin", back_populates="player")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    icon = Column(String(10), nullable=False)
    quantity = Column(Integer, default=1)
    item_type = Column(String(50), default="material")
    rarity = Column(String(20), default="common")
    
    player = relationship("Player", back_populates="inventory")


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), unique=True, nullable=False)
    
    weapon_name = Column(String(100), nullable=True)
    weapon_icon = Column(String(10), nullable=True)
    weapon_attack = Column(Integer, default=0)
    
    armor_name = Column(String(100), nullable=True)
    armor_icon = Column(String(10), nullable=True)
    armor_defense = Column(Integer, default=0)
    
    accessory_name = Column(String(100), nullable=True)
    accessory_icon = Column(String(10), nullable=True)
    
    player = relationship("Player", back_populates="equipment")


class OwnedSkin(Base):
    __tablename__ = "owned_skins"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    skin_id = Column(String(50), nullable=False)
    
    player = relationship("Player", back_populates="owned_skins")


class MarketListing(Base):
    __tablename__ = "market_listings"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    item_name = Column(String(100), nullable=False)
    item_icon = Column(String(10), nullable=False)
    item_rarity = Column(String(20), default="common")
    
    price = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    seller = relationship("Player")