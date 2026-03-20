from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    name = Column(String)
    role = Column(String)  # owner / worker
    is_active = Column(Boolean, default=True)