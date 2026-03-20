from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from app.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    category = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    comment = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)