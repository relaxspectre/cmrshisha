from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sale import Sale
from app.models.shift import Shift
from app.models.user import User


def get_shift_report(db: Session, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    last_shift = (
        db.query(Shift)
        .filter(Shift.user_id == user.id)
        .order_by(Shift.id.desc())
        .first()
    )

    if not last_shift:
        return {"ok": False, "message": "Змін не знайдено."}

    sales = db.query(Sale).filter(Sale.shift_id == last_shift.id).all()

    total_sales_count = sum(s.quantity for s in sales)
    total_revenue = sum(float(s.total_price) for s in sales)

    return {
        "ok": True,
        "shift_id": last_shift.id,
        "status": last_shift.status,
        "sales_count": total_sales_count,
        "revenue": total_revenue,
    }