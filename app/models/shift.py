from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from datetime import datetime

from app.core.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    status = Column(String, default="active", nullable=False)