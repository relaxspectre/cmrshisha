from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    movement_type = Column(String, nullable=False)  # income / sale / writeoff / correction
    grams = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)