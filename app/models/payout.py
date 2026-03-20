from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from app.core.database import Base


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    comment = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)