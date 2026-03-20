import json
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.database import SessionLocal
from app.models.user import User

router = APIRouter()


class AuthRequest(BaseModel):
    initData: str
@router.post("/auth")
async def auth(data: AuthRequest):
    print("INIT DATA RAW:", data.initData)
    return {"status": "ok"}