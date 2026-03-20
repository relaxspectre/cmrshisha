from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


class Writeoff(Base):
    __tablename__ = "writeoffs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True)

    tobacco_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)