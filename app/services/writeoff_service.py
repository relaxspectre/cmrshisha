from sqlalchemy.orm import Session

from app.models.shift import Shift
from app.models.user import User
from app.models.writeoff import Writeoff
from app.services.inventory_service import consume_inventory_writeoff


def add_writeoff(
    db: Session,
    telegram_id: str,
    tobacco_name: str,
    quantity: int,
    comment: str,
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    active_shift = (
        db.query(Shift)
        .filter(Shift.user_id == user.id, Shift.status == "active")
        .first()
    )

    if not active_shift:
        return {"ok": False, "message": "Немає активної зміни."}

    if quantity <= 0:
        return {"ok": False, "message": "Кількість має бути більше 0."}

    inventory_result = consume_inventory_writeoff(
        db=db,
        user_id=user.id,
        tobacco_name=tobacco_name,
        grams=quantity,
        comment=comment,
    )

    if not inventory_result["ok"]:
        db.rollback()
        return inventory_result

    writeoff = Writeoff(
        user_id=user.id,
        shift_id=active_shift.id,
        tobacco_name=tobacco_name,
        quantity=quantity,
        comment=comment,
    )

    db.add(writeoff)
    db.commit()
    db.refresh(writeoff)

    return {
        "ok": True,
        "message": "Списання збережено.",
        "writeoff_id": writeoff.id,
        "grams_left": inventory_result["grams_remaining"],
    }