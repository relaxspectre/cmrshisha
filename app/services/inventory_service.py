from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.inventory_movement import InventoryMovement
from app.models.user import User

PREMIUM_NAME = "Premium"
HARD_NAME = "Hard"
LOW_STOCK_LIMIT = 1300


def _normalize_category(value: str) -> str | None:
    value = (value or "").strip().lower()

    if value in ("premium", "преміум"):
        return PREMIUM_NAME

    if value in ("hard", "хард"):
        return HARD_NAME

    return None


def _get_or_create_category_item(db: Session, name: str) -> InventoryItem:
    item = db.query(InventoryItem).filter(InventoryItem.name == name).first()

    if not item:
        item = InventoryItem(
            name=name,
            grams_remaining=0,
            is_active=True,
        )
        db.add(item)
        db.flush()

    return item


def ensure_base_inventory_categories(db: Session):
    _get_or_create_category_item(db, PREMIUM_NAME)
    _get_or_create_category_item(db, HARD_NAME)
    db.commit()


def get_inventory_items(db: Session):
    ensure_base_inventory_categories(db)

    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.name.in_([PREMIUM_NAME, HARD_NAME]))
        .order_by(InventoryItem.name.asc())
        .all()
    )

    return [
        {
            "id": item.id,
            "name": item.name,
            "grams_remaining": item.grams_remaining,
        }
        for item in items
    ]


def get_inventory_summary(db: Session, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    if user.role != "owner":
        return {"ok": False, "message": "Тільки власник бачить склад."}

    ensure_base_inventory_categories(db)

    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.name.in_([PREMIUM_NAME, HARD_NAME]))
        .order_by(InventoryItem.name.asc())
        .all()
    )

    total_grams = sum(item.grams_remaining for item in items)

    return {
        "ok": True,
        "total_grams": total_grams,
        "items": [
            {
                "name": item.name,
                "grams_remaining": item.grams_remaining,
            }
            for item in items
        ],
    }


def get_inventory_status_for_user(db: Session, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    if user.role not in ("owner", "worker"):
        return {"ok": False, "message": "Немає доступу до складу."}

    ensure_base_inventory_categories(db)

    premium = _get_or_create_category_item(db, PREMIUM_NAME)
    hard = _get_or_create_category_item(db, HARD_NAME)

    return {
        "ok": True,
        "premium_grams": premium.grams_remaining,
        "hard_grams": hard.grams_remaining,
        "total_grams": premium.grams_remaining + hard.grams_remaining,
        "items": [
            {"name": PREMIUM_NAME, "grams_remaining": premium.grams_remaining},
            {"name": HARD_NAME, "grams_remaining": hard.grams_remaining},
        ],
        "premium_low": premium.grams_remaining < LOW_STOCK_LIMIT,
        "hard_low": hard.grams_remaining < LOW_STOCK_LIMIT,
        "limit": LOW_STOCK_LIMIT,
    }


def add_inventory_income(
    db: Session,
    telegram_id: str,
    tobacco_name: str,
    grams: int,
    comment: str,
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    if user.role != "owner":
        return {"ok": False, "message": "Тільки власник може додавати прихід."}

    category_name = _normalize_category(tobacco_name)
    if not category_name:
        return {"ok": False, "message": "Доступно тільки 2 категорії: Premium або Hard."}

    if grams <= 0:
        return {"ok": False, "message": "Кількість грам має бути більше 0."}

    item = _get_or_create_category_item(db, category_name)
    item.grams_remaining += grams

    movement = InventoryMovement(
        item_id=item.id,
        user_id=user.id,
        movement_type="income",
        grams=grams,
        comment=comment,
    )

    db.add(movement)
    db.commit()
    db.refresh(item)

    return {
        "ok": True,
        "message": "Прихід на склад додано.",
        "item_name": item.name,
        "grams_remaining": item.grams_remaining,
    }


def consume_inventory_for_sale(
    db: Session,
    user_id: int,
    tobacco_name: str,
    grams: int,
    comment: str,
):
    category_name = _normalize_category(tobacco_name)
    if not category_name:
        return {"ok": False, "message": "Продаж можливий тільки для Premium або Hard."}

    item = _get_or_create_category_item(db, category_name)

    if item.grams_remaining < grams:
        return {
            "ok": False,
            "message": f"Недостатньо табаку '{item.name}' на складі. Залишок: {item.grams_remaining} г."
        }

    item.grams_remaining -= grams

    movement = InventoryMovement(
        item_id=item.id,
        user_id=user_id,
        movement_type="sale",
        grams=-grams,
        comment=comment,
    )

    db.add(movement)
    db.flush()

    warning = None
    if item.grams_remaining < LOW_STOCK_LIMIT:
        warning = (
            f"⚠️ Низький залишок {item.name}\n"
            f"📦 Залишок: {item.grams_remaining} г\n"
            f"🔻 Мінімум: {LOW_STOCK_LIMIT} г"
        )

    return {
        "ok": True,
        "item_name": item.name,
        "grams_remaining": item.grams_remaining,
        "warning": warning,
    }


def consume_inventory_writeoff(
    db: Session,
    user_id: int,
    tobacco_name: str,
    grams: int,
    comment: str,
):
    category_name = _normalize_category(tobacco_name)
    if not category_name:
        return {"ok": False, "message": "Списання можливе тільки для Premium або Hard."}

    if grams <= 0:
        return {"ok": False, "message": "Кількість має бути більше 0."}

    item = _get_or_create_category_item(db, category_name)

    if item.grams_remaining < grams:
        return {
            "ok": False,
            "message": f"Недостатньо табаку '{item.name}' на складі. Залишок: {item.grams_remaining} г."
        }

    item.grams_remaining -= grams

    movement = InventoryMovement(
        item_id=item.id,
        user_id=user_id,
        movement_type="writeoff",
        grams=-grams,
        comment=comment,
    )

    db.add(movement)
    db.flush()

    warning = None
    if item.grams_remaining < LOW_STOCK_LIMIT:
        warning = (
            f"⚠️ Низький залишок {item.name}\n"
            f"📦 Залишок: {item.grams_remaining} г\n"
            f"🔻 Мінімум: {LOW_STOCK_LIMIT} г"
        )

    return {
        "ok": True,
        "item_name": item.name,
        "grams_remaining": item.grams_remaining,
        "warning": warning,
    }


def get_low_stock_alerts(db: Session):
    ensure_base_inventory_categories(db)

    premium = _get_or_create_category_item(db, PREMIUM_NAME)
    hard = _get_or_create_category_item(db, HARD_NAME)

    alerts = []

    if premium.grams_remaining < LOW_STOCK_LIMIT:
        alerts.append(
            f"⚠️ Низький залишок PREMIUM\n"
            f"📦 Залишок: {premium.grams_remaining} г\n"
            f"🔻 Мінімум: {LOW_STOCK_LIMIT} г\n"
            f"Потрібно закупити Premium."
        )

    if hard.grams_remaining < LOW_STOCK_LIMIT:
        alerts.append(
            f"⚠️ Низький залишок HARD\n"
            f"📦 Залишок: {hard.grams_remaining} г\n"
            f"🔻 Мінімум: {LOW_STOCK_LIMIT} г\n"
            f"Потрібно закупити Hard."
        )

    return alerts