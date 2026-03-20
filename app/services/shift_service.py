from datetime import datetime

from sqlalchemy.orm import Session

from app.models.sale import Sale
from app.models.shift import Shift
from app.models.user import User
from app.models.writeoff import Writeoff


def start_shift(db: Session, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    active_shift = (
        db.query(Shift)
        .filter(Shift.user_id == user.id, Shift.status == "active")
        .first()
    )

    if active_shift:
        return {"ok": False, "message": "У тебе вже є активна зміна."}

    new_shift = Shift(user_id=user.id, status="active")
    db.add(new_shift)
    db.commit()
    db.refresh(new_shift)

    return {
        "ok": True,
        "message": "Зміну успішно відкрито.",
        "shift_id": new_shift.id,
    }


def end_shift(db: Session, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    shift = (
        db.query(Shift)
        .filter(Shift.user_id == user.id, Shift.status == "active")
        .first()
    )

    if not shift:
        return {"ok": False, "message": "Немає активної зміни."}

    sales = db.query(Sale).filter(Sale.shift_id == shift.id).all()
    writeoffs_count = db.query(Writeoff).filter(Writeoff.shift_id == shift.id).count()

    total_sales_count = sum(s.quantity for s in sales)
    total_revenue = sum(float(s.total_price) for s in sales)

    shift.ended_at = datetime.utcnow()
    shift.status = "closed"

    duration = shift.ended_at - shift.started_at

    db.commit()

    return {
        "ok": True,
        "message": "Зміну закрито",
        "shift_id": shift.id,
        "duration_minutes": int(duration.total_seconds() // 60),
        "sales_count": total_sales_count,
        "revenue": total_revenue,
        "writeoffs_count": writeoffs_count,
    }