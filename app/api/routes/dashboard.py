from fastapi import APIRouter, HTTPException

from app.core.database import SessionLocal
from app.models.user import User
from app.services.dashboard_service import (
    get_cash_summary,
    get_owner_dashboard,
    get_owner_payouts,
    get_statistics_summary,
    get_worker_dashboard,
    get_workers_stats,
)
from app.services.inventory_service import (
    get_inventory_status_for_user,
    get_inventory_summary,
)

router = APIRouter(tags=["dashboard"])


@router.get("/me/{telegram_id}")
def me(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Користувача не знайдено.")

        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
        }
    finally:
        db.close()


@router.get("/workers-list/{telegram_id}")
def workers_list(telegram_id: str):
    db = SessionLocal()
    try:
        requester = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not requester:
            raise HTTPException(status_code=404, detail="Користувача не знайдено.")

        if requester.role != "owner":
            raise HTTPException(status_code=403, detail="Тільки власник має доступ.")

        workers = (
            db.query(User)
            .filter(User.role == "worker", User.is_active.is_(True))
            .order_by(User.name.asc())
            .all()
        )

        return {
            "ok": True,
            "items": [
                {
                    "id": worker.id,
                    "telegram_id": worker.telegram_id,
                    "name": worker.name,
                }
                for worker in workers
            ],
        }
    finally:
        db.close()


@router.get("/stock/{telegram_id}")
def stock(telegram_id: str):
    db = SessionLocal()
    try:
        result = get_inventory_status_for_user(db, telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=403, detail=result["message"])
        return result
    finally:
        db.close()


@router.get("/worker-dashboard/{telegram_id}")
def worker_dashboard(telegram_id: str):
    db = SessionLocal()
    try:
        result = get_worker_dashboard(db, telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    finally:
        db.close()


@router.get("/owner-dashboard/{telegram_id}")
def owner_dashboard(telegram_id: str):
    db = SessionLocal()
    try:
        result = get_owner_dashboard(db, telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=403, detail=result["message"])
        return result
    finally:
        db.close()


@router.get("/cash/{telegram_id}")
def cash(telegram_id: str):
    db = SessionLocal()
    try:
        result = get_cash_summary(db, telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=403, detail=result["message"])
        return result
    finally:
        db.close()


@router.get("/statistics/{telegram_id}")
def statistics(telegram_id: str):
    db = SessionLocal()
    try:
        result = get_statistics_summary(db, telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=403, detail=result["message"])
        return result
    finally:
        db.close()


@router.get("/inventory/{telegram_id}")
def inventory(telegram_id: str):
    db = SessionLocal()
    try:
        result = get_inventory_summary(db, telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=403, detail=result["message"])
        return result
    finally:
        db.close()


@router.get("/workers/{telegram_id}")
def workers(telegram_id: str):
    db = SessionLocal()
    try:
        result = get_workers_stats(db, telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=403, detail=result["message"])
        return result
    finally:
        db.close()


@router.get("/owner-payouts/{telegram_id}")
def owner_payouts(telegram_id: str):
    db = SessionLocal()
    try:
        result = get_owner_payouts(db, telegram_id)
        if not result["ok"]:
            raise HTTPException(status_code=403, detail=result["message"])
        return result
    finally:
        db.close()