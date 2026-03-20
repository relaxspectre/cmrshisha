from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.user import User


def add_expense(
    db: Session,
    telegram_id: str,
    category: str,
    amount: float,
    comment: str,
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    if user.role != "owner":
        return {"ok": False, "message": "Тільки власник може вносити витрати."}

    if amount <= 0:
        return {"ok": False, "message": "Сума має бути більше 0."}

    expense = Expense(
        user_id=user.id,
        category=category,
        amount=Decimal(str(amount)),
        comment=comment,
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return {
        "ok": True,
        "message": "Витрату додано.",
        "expense_id": expense.id,
        "amount": float(expense.amount),
    }