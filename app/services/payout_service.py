from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.payout import Payout
from app.models.user import User


def add_payout(
    db: Session,
    owner_telegram_id: str,
    worker_telegram_id: str,
    amount: float,
    comment: str,
):
    owner = db.query(User).filter(User.telegram_id == owner_telegram_id).first()

    if not owner:
        return {"ok": False, "message": "Власника не знайдено."}

    if owner.role != "owner":
        return {"ok": False, "message": "Тільки власник може вносити виплати."}

    worker = db.query(User).filter(User.telegram_id == worker_telegram_id).first()

    if not worker:
        return {"ok": False, "message": "Працівника не знайдено."}

    if worker.role != "worker":
        return {"ok": False, "message": "Виплату можна вносити тільки працівнику."}

    if amount <= 0:
        return {"ok": False, "message": "Сума має бути більше 0."}

    payout = Payout(
        user_id=worker.id,
        created_by=owner.id,
        amount=Decimal(str(amount)),
        comment=comment,
    )

    db.add(payout)
    db.commit()
    db.refresh(payout)

    return {
        "ok": True,
        "message": "Виплату додано.",
        "payout_id": payout.id,
        "worker_name": worker.name,
        "amount": float(payout.amount),
    }


def get_my_payouts(db: Session, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    payouts = (
        db.query(Payout)
        .filter(Payout.user_id == user.id)
        .order_by(Payout.id.desc())
        .all()
    )

    total_amount = sum(float(p.amount) for p in payouts)

    items = []
    for p in payouts[:10]:
        items.append(
            {
                "id": p.id,
                "amount": float(p.amount),
                "comment": p.comment or "-",
                "created_at": p.created_at.strftime("%d.%m.%Y %H:%M"),
            }
        )

    return {
        "ok": True,
        "total_amount": total_amount,
        "count": len(payouts),
        "items": items,
    }


def get_workers_list(db: Session):
    workers = (
        db.query(User)
        .filter(User.role == "worker", User.is_active == True)
        .order_by(User.name.asc())
        .all()
    )

    return [
        {
            "telegram_id": w.telegram_id,
            "name": w.name,
        }
        for w in workers
    ]