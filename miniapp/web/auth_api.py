import hashlib
import hmac
import json
import os
from urllib.parse import parse_qsl

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.database import SessionLocal
from app.models.user import User

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not found in .env")

app = FastAPI()


class TelegramAuthRequest(BaseModel):
    init_data: str


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=400, detail="hash not found in init_data")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="invalid Telegram signature")

    user_raw = pairs.get("user")
    if not user_raw:
        raise HTTPException(status_code=400, detail="user not found in init_data")

    try:
        user_data = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid user json")

    return user_data


@app.post("/api/auth/telegram")
def telegram_auth(payload: TelegramAuthRequest):
    tg_user = validate_telegram_init_data(payload.init_data, BOT_TOKEN)

    telegram_id = str(tg_user["id"])
    name = tg_user.get("first_name") or tg_user.get("username") or "Telegram User"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            user = User(
                telegram_id=telegram_id,
                name=name,
                role="worker",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return {
            "ok": True,
            "user": {
                "telegram_id": user.telegram_id,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
            },
        }
    finally:
        db.close()