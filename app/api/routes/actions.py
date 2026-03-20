from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.database import SessionLocal
from app.models.user import User
from app.services.sale_service import add_sale
from app.services.shift_service import end_shift, start_shift

router = APIRouter(tags=["actions"])


class StartShiftBody(BaseModel):
    telegram_id: str


class EndShiftBody(BaseModel):
    telegram_id: str


class AddSaleBody(BaseModel):
    telegram_id: str
    category: str
    quantity: int = Field(ge=1)


class OwnerAddSaleBody(BaseModel):
    telegram_id: str
    worker_telegram_id: str
    category: str
    quantity: int = Field(ge=1)
    date: str  # YYYY-MM-DD
    time: str  # HH:MM


@router.post("/start-shift")
def start_shift_api(body: StartShiftBody):
    db = SessionLocal()
    try:
        result = start_shift(db, body.telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    finally:
        db.close()


@router.post("/end-shift")
def end_shift_api(body: EndShiftBody):
    db = SessionLocal()
    try:
        result = end_shift(db, body.telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    finally:
        db.close()


@router.post("/add-sale")
def add_sale_api(body: AddSaleBody):
    db = SessionLocal()
    try:
        category = body.category.strip().lower()

        if category == "premium":
            product_name = "Premium Hookah"
            tobacco_name = "Premium"
            unit_price = 225
        elif category == "hard":
            product_name = "Hard Hookah"
            tobacco_name = "Hard"
            unit_price = 235
        else:
            raise HTTPException(status_code=400, detail="Категорія має бути premium або hard.")

        result = add_sale(
            db=db,
            telegram_id=body.telegram_id,
            product_name=product_name,
            tobacco_name=tobacco_name,
            quantity=body.quantity,
            unit_price=unit_price,
        )

        if not result["ok"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result
    finally:
        db.close()


@router.post("/owner-add-sale")
def owner_add_sale_api(body: OwnerAddSaleBody):
    db = SessionLocal()
    try:
        requester = db.query(User).filter(User.telegram_id == body.telegram_id).first()
        if not requester:
            raise HTTPException(status_code=404, detail="Користувача не знайдено.")

        if requester.role != "owner":
            raise HTTPException(status_code=403, detail="Тільки власник може додавати продаж заднім числом.")

        worker = db.query(User).filter(User.telegram_id == body.worker_telegram_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="Працівника не знайдено.")

        if worker.role != "worker":
            raise HTTPException(status_code=400, detail="Обраний користувач не є працівником.")

        category = body.category.strip().lower()
        if category == "premium":
            product_name = "Premium Hookah"
            tobacco_name = "Premium"
            unit_price = 225
        elif category == "hard":
            product_name = "Hard Hookah"
            tobacco_name = "Hard"
            unit_price = 235
        else:
            raise HTTPException(status_code=400, detail="Категорія має бути premium або hard.")

        try:
            custom_datetime = datetime.strptime(
                f"{body.date} {body.time}",
                "%Y-%m-%d %H:%M",
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Невірний формат дати або часу.")

        result = add_sale(
            db=db,
            telegram_id=body.worker_telegram_id,
            product_name=product_name,
            tobacco_name=tobacco_name,
            quantity=body.quantity,
            unit_price=unit_price,
            custom_datetime=custom_datetime,
            allow_without_active_shift=True,
        )

        if not result["ok"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result
    finally:
        db.close()