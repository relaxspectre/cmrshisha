from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.payout import Payout
from app.models.sale import Sale
from app.models.user import User
from app.models.writeoff import Writeoff


def _check_owner(db: Session, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return None, {"ok": False, "message": "Користувача не знайдено."}

    if user.role != "owner":
        return None, {"ok": False, "message": "Тільки власник має доступ."}

    return user, None


def delete_last_sale(db: Session, telegram_id: str):
    _, error = _check_owner(db, telegram_id)
    if error:
        return error

    item = db.query(Sale).order_by(Sale.id.desc()).first()
    if not item:
        return {"ok": False, "message": "Продажів немає."}

    info = f"{item.product_name} | {item.quantity} шт | {float(item.total_price)} грн"
    db.delete(item)
    db.commit()

    return {"ok": True, "message": f"Останній продаж видалено: {info}"}


def delete_last_expense(db: Session, telegram_id: str):
    _, error = _check_owner(db, telegram_id)
    if error:
        return error

    item = db.query(Expense).order_by(Expense.id.desc()).first()
    if not item:
        return {"ok": False, "message": "Витрат немає."}

    info = f"{item.category} | {float(item.amount)} грн"
    db.delete(item)
    db.commit()

    return {"ok": True, "message": f"Останню витрату видалено: {info}"}


def delete_last_payout(db: Session, telegram_id: str):
    _, error = _check_owner(db, telegram_id)
    if error:
        return error

    item = db.query(Payout).order_by(Payout.id.desc()).first()
    if not item:
        return {"ok": False, "message": "Виплат немає."}

    worker = db.query(User).filter(User.id == item.user_id).first()
    worker_name = worker.name if worker else f"ID {item.user_id}"
    info = f"{worker_name} | {float(item.amount)} грн"
    db.delete(item)
    db.commit()

    return {"ok": True, "message": f"Останню виплату видалено: {info}"}


def delete_last_writeoff(db: Session, telegram_id: str):
    _, error = _check_owner(db, telegram_id)
    if error:
        return error

    item = db.query(Writeoff).order_by(Writeoff.id.desc()).first()
    if not item:
        return {"ok": False, "message": "Списань немає."}

    info = f"{item.tobacco_name} | {item.quantity}"
    db.delete(item)
    db.commit()

    return {"ok": True, "message": f"Останнє списання видалено: {info}"}