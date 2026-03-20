from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from app.core.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    product_name = Column(String, nullable=False)
    tobacco_name = Column(String, nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)