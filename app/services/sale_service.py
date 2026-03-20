from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.sale import Sale
from app.models.shift import Shift
from app.models.user import User
from app.services.inventory_service import consume_inventory_for_sale

GRAMS_PER_HOOKAH = 21


def _get_or_create_sale_shift(
    db: Session,
    user_id: int,
    sale_time: datetime,
    allow_without_active_shift: bool,
):
    if not allow_without_active_shift:
        return (
            db.query(Shift)
            .filter(Shift.user_id == user_id, Shift.status == "active")
            .first()
        )

    existing_shift = (
        db.query(Shift)
        .filter(
            Shift.user_id == user_id,
            Shift.started_at <= sale_time,
            Shift.ended_at >= sale_time,
        )
        .order_by(Shift.started_at.desc())
        .first()
    )

    if existing_shift:
        return existing_shift

    shift = Shift(
        user_id=user_id,
        started_at=sale_time,
        ended_at=sale_time + timedelta(minutes=1),
        status="closed",
    )
    db.add(shift)
    db.flush()
    return shift


def add_sale(
    db: Session,
    telegram_id: str,
    product_name: str,
    tobacco_name: str,
    quantity: int,
    unit_price: float,
    custom_datetime: datetime | None = None,
    allow_without_active_shift: bool = False,
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    if quantity <= 0:
        return {"ok": False, "message": "Кількість має бути більше 0."}

    if unit_price <= 0:
        return {"ok": False, "message": "Ціна має бути більше 0."}

    sale_time = custom_datetime or datetime.utcnow()

    shift = _get_or_create_sale_shift(
        db=db,
        user_id=user.id,
        sale_time=sale_time,
        allow_without_active_shift=allow_without_active_shift,
    )

    if not shift:
        return {"ok": False, "message": "Немає активної зміни."}

    grams_to_consume = GRAMS_PER_HOOKAH * quantity

    inventory_result = consume_inventory_for_sale(
        db=db,
        user_id=user.id,
        tobacco_name=tobacco_name,
        grams=grams_to_consume,
        comment=f"Продаж {product_name}, {quantity} шт",
    )

    if not inventory_result["ok"]:
        db.rollback()
        return inventory_result

    total_price = Decimal(str(quantity)) * Decimal(str(unit_price))

    sale = Sale(
        shift_id=shift.id,
        product_name=product_name,
        tobacco_name=inventory_result["item_name"],
        quantity=quantity,
        unit_price=Decimal(str(unit_price)),
        total_price=total_price,
        created_at=sale_time,
    )

    db.add(sale)
    db.commit()
    db.refresh(sale)

    return {
        "ok": True,
        "message": "Продаж додано.",
        "sale_id": sale.id,
        "shift_id": shift.id,
        "total_price": float(sale.total_price),
        "tobacco_name": inventory_result["item_name"],
        "grams_written_off": grams_to_consume,
        "inventory_left": inventory_result["grams_remaining"],
    }