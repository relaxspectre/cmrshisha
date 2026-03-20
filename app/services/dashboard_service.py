from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.inventory_item import InventoryItem
from app.models.payout import Payout
from app.models.sale import Sale
from app.models.shift import Shift
from app.models.user import User
from app.models.writeoff import Writeoff

PREMIUM_COST = 68
HARD_COST = 72


def _today_range():
    now = datetime.utcnow()
    start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)
    return start, end


def _month_range():
    now = datetime.utcnow()
    start = datetime(now.year, now.month, 1)

    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)

    return start, end


def _last_week_range():
    now = datetime.utcnow()
    start_of_this_week = now - timedelta(days=now.weekday())
    start_of_this_week = start_of_this_week.replace(hour=0, minute=0, second=0, microsecond=0)

    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week

    return start_of_last_week, end_of_last_week


def _calc_cogs(sales):
    total = 0.0
    for sale in sales:
        if sale.product_name == "Premium Hookah":
            total += PREMIUM_COST * sale.quantity
        elif sale.product_name == "Hard Hookah":
            total += HARD_COST * sale.quantity
    return total


def get_worker_dashboard(db: Session, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return {"ok": False, "message": "Користувача не знайдено."}

    today_start, today_end = _today_range()
    month_start, month_end = _month_range()

    active_shift = (
        db.query(Shift)
        .filter(Shift.user_id == user.id, Shift.status == "active")
        .order_by(Shift.id.desc())
        .first()
    )

    current_shift_sales_count = 0
    current_shift_revenue = 0.0
    current_shift_writeoffs = 0

    if active_shift:
        current_sales = db.query(Sale).filter(Sale.shift_id == active_shift.id).all()
        current_shift_sales_count = sum(s.quantity for s in current_sales)
        current_shift_revenue = sum(float(s.total_price) for s in current_sales)

        current_shift_writeoffs = (
            db.query(Writeoff)
            .filter(Writeoff.shift_id == active_shift.id)
            .count()
        )

    today_shifts = (
        db.query(Shift)
        .filter(
            Shift.user_id == user.id,
            Shift.started_at >= today_start,
            Shift.started_at < today_end,
        )
        .all()
    )
    today_shift_ids = [s.id for s in today_shifts]

    month_shifts = (
        db.query(Shift)
        .filter(
            Shift.user_id == user.id,
            Shift.started_at >= month_start,
            Shift.started_at < month_end,
        )
        .all()
    )
    month_shift_ids = [s.id for s in month_shifts]

    today_sales = []
    if today_shift_ids:
        today_sales = db.query(Sale).filter(Sale.shift_id.in_(today_shift_ids)).all()

    month_sales = []
    if month_shift_ids:
        month_sales = db.query(Sale).filter(Sale.shift_id.in_(month_shift_ids)).all()

    today_hooks = sum(s.quantity for s in today_sales)
    today_revenue = sum(float(s.total_price) for s in today_sales)

    month_hooks = sum(s.quantity for s in month_sales)
    month_revenue = sum(float(s.total_price) for s in month_sales)

    payout_total = db.query(Payout).filter(Payout.user_id == user.id).all()
    total_paid = sum(float(p.amount) for p in payout_total)

    return {
        "ok": True,
        "shift_active": active_shift is not None,
        "current_shift_hooks": current_shift_sales_count,
        "current_shift_revenue": current_shift_revenue,
        "current_shift_writeoffs": current_shift_writeoffs,
        "today_hooks": today_hooks,
        "today_revenue": today_revenue,
        "month_hooks": month_hooks,
        "month_revenue": month_revenue,
        "total_paid": total_paid,
    }


def get_owner_dashboard(db: Session, telegram_id: str):
    owner = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not owner:
        return {"ok": False, "message": "Користувача не знайдено."}

    if owner.role != "owner":
        return {"ok": False, "message": "Тільки власник бачить цей дашборд."}

    today_start, today_end = _today_range()
    month_start, month_end = _month_range()

    today_sales = db.query(Sale).filter(Sale.created_at >= today_start, Sale.created_at < today_end).all()
    month_sales = db.query(Sale).filter(Sale.created_at >= month_start, Sale.created_at < month_end).all()

    today_expenses = db.query(Expense).filter(Expense.created_at >= today_start, Expense.created_at < today_end).all()
    month_expenses = db.query(Expense).filter(Expense.created_at >= month_start, Expense.created_at < month_end).all()

    today_payouts = db.query(Payout).filter(Payout.created_at >= today_start, Payout.created_at < today_end).all()
    month_payouts = db.query(Payout).filter(Payout.created_at >= month_start, Payout.created_at < month_end).all()

    today_writeoffs = db.query(Writeoff).filter(Writeoff.created_at >= today_start, Writeoff.created_at < today_end).count()
    month_writeoffs = db.query(Writeoff).filter(Writeoff.created_at >= month_start, Writeoff.created_at < month_end).count()

    active_shifts = db.query(Shift).filter(Shift.status == "active").all()
    active_user_ids = [s.user_id for s in active_shifts]

    active_workers = []
    if active_user_ids:
        active_workers = db.query(User).filter(User.id.in_(active_user_ids)).all()

    today_revenue = sum(float(s.total_price) for s in today_sales)
    month_revenue = sum(float(s.total_price) for s in month_sales)

    today_cogs = _calc_cogs(today_sales)
    month_cogs = _calc_cogs(month_sales)

    today_exp_sum = sum(float(e.amount) for e in today_expenses)
    month_exp_sum = sum(float(e.amount) for e in month_expenses)

    today_payout_sum = sum(float(p.amount) for p in today_payouts)
    month_payout_sum = sum(float(p.amount) for p in month_payouts)

    return {
        "ok": True,
        "today_hooks": sum(s.quantity for s in today_sales),
        "today_revenue": today_revenue,
        "today_cogs": today_cogs,
        "today_gross_profit": today_revenue - today_cogs,
        "today_expenses": today_exp_sum,
        "today_payouts": today_payout_sum,
        "today_net_profit": today_revenue - today_cogs - today_exp_sum - today_payout_sum,
        "today_writeoffs": today_writeoffs,
        "month_hooks": sum(s.quantity for s in month_sales),
        "month_revenue": month_revenue,
        "month_cogs": month_cogs,
        "month_gross_profit": month_revenue - month_cogs,
        "month_expenses": month_exp_sum,
        "month_payouts": month_payout_sum,
        "month_net_profit": month_revenue - month_cogs - month_exp_sum - month_payout_sum,
        "month_writeoffs": month_writeoffs,
        "active_workers_count": len(active_workers),
        "active_workers_names": [u.name for u in active_workers],
    }


def get_cash_summary(db: Session, telegram_id: str):
    owner = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not owner:
        return {"ok": False, "message": "Користувача не знайдено."}

    if owner.role != "owner":
        return {"ok": False, "message": "Тільки власник бачить касу."}

    sales = db.query(Sale).all()
    expenses = db.query(Expense).all()
    payouts = db.query(Payout).all()

    revenue = sum(float(s.total_price) for s in sales)
    hooks = sum(s.quantity for s in sales)
    expenses_sum = sum(float(e.amount) for e in expenses)
    payouts_sum = sum(float(p.amount) for p in payouts)

    return {
        "ok": True,
        "hooks": hooks,
        "revenue": revenue,
        "expenses": expenses_sum,
        "payouts": payouts_sum,
        "cash": revenue - expenses_sum - payouts_sum,
    }


def get_statistics_summary(db: Session, telegram_id: str):
    owner = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not owner:
        return {"ok": False, "message": "Користувача не знайдено."}

    if owner.role != "owner":
        return {"ok": False, "message": "Тільки власник бачить статистику."}

    today_start, today_end = _today_range()
    month_start, month_end = _month_range()
    last_week_start, last_week_end = _last_week_range()

    today_sales = db.query(Sale).filter(Sale.created_at >= today_start, Sale.created_at < today_end).all()
    month_sales = db.query(Sale).filter(Sale.created_at >= month_start, Sale.created_at < month_end).all()
    last_week_sales = db.query(Sale).filter(Sale.created_at >= last_week_start, Sale.created_at < last_week_end).all()

    today_expenses = db.query(Expense).filter(Expense.created_at >= today_start, Expense.created_at < today_end).all()
    month_expenses = db.query(Expense).filter(Expense.created_at >= month_start, Expense.created_at < month_end).all()
    last_week_expenses = db.query(Expense).filter(Expense.created_at >= last_week_start, Expense.created_at < last_week_end).all()

    today_payouts = db.query(Payout).filter(Payout.created_at >= today_start, Payout.created_at < today_end).all()
    month_payouts = db.query(Payout).filter(Payout.created_at >= month_start, Payout.created_at < month_end).all()
    last_week_payouts = db.query(Payout).filter(Payout.created_at >= last_week_start, Payout.created_at < last_week_end).all()

    today_writeoffs = db.query(Writeoff).filter(Writeoff.created_at >= today_start, Writeoff.created_at < today_end).count()
    month_writeoffs = db.query(Writeoff).filter(Writeoff.created_at >= month_start, Writeoff.created_at < month_end).count()
    last_week_writeoffs = db.query(Writeoff).filter(Writeoff.created_at >= last_week_start, Writeoff.created_at < last_week_end).count()

    workers = (
        db.query(User)
        .filter(User.role == "worker", User.is_active == True)
        .order_by(User.name.asc())
        .all()
    )

    worker_items = []

    for worker in workers:
        shifts = (
            db.query(Shift)
            .filter(
                Shift.user_id == worker.id,
                Shift.started_at >= month_start,
                Shift.started_at < month_end,
            )
            .all()
        )
        shift_ids = [s.id for s in shifts]

        sales = []
        if shift_ids:
            sales = db.query(Sale).filter(Sale.shift_id.in_(shift_ids)).all()

        worker_items.append(
            {
                "name": worker.name,
                "hooks": sum(s.quantity for s in sales),
                "revenue": sum(float(s.total_price) for s in sales),
            }
        )

    today_revenue = sum(float(s.total_price) for s in today_sales)
    last_week_revenue = sum(float(s.total_price) for s in last_week_sales)
    month_revenue = sum(float(s.total_price) for s in month_sales)

    today_cogs = _calc_cogs(today_sales)
    last_week_cogs = _calc_cogs(last_week_sales)
    month_cogs = _calc_cogs(month_sales)

    today_exp_sum = sum(float(e.amount) for e in today_expenses)
    last_week_exp_sum = sum(float(e.amount) for e in last_week_expenses)
    month_exp_sum = sum(float(e.amount) for e in month_expenses)

    today_payout_sum = sum(float(p.amount) for p in today_payouts)
    last_week_payout_sum = sum(float(p.amount) for p in last_week_payouts)
    month_payout_sum = sum(float(p.amount) for p in month_payouts)

    return {
        "ok": True,
        "today_hooks": sum(s.quantity for s in today_sales),
        "today_revenue": today_revenue,
        "today_cogs": today_cogs,
        "today_gross_profit": today_revenue - today_cogs,
        "today_expenses": today_exp_sum,
        "today_payouts": today_payout_sum,
        "today_net_profit": today_revenue - today_cogs - today_exp_sum - today_payout_sum,
        "today_writeoffs": today_writeoffs,
        "last_week_hooks": sum(s.quantity for s in last_week_sales),
        "last_week_revenue": last_week_revenue,
        "last_week_cogs": last_week_cogs,
        "last_week_gross_profit": last_week_revenue - last_week_cogs,
        "last_week_expenses": last_week_exp_sum,
        "last_week_payouts": last_week_payout_sum,
        "last_week_net_profit": last_week_revenue - last_week_cogs - last_week_exp_sum - last_week_payout_sum,
        "last_week_writeoffs": last_week_writeoffs,
        "month_hooks": sum(s.quantity for s in month_sales),
        "month_revenue": month_revenue,
        "month_cogs": month_cogs,
        "month_gross_profit": month_revenue - month_cogs,
        "month_expenses": month_exp_sum,
        "month_payouts": month_payout_sum,
        "month_net_profit": month_revenue - month_cogs - month_exp_sum - month_payout_sum,
        "month_writeoffs": month_writeoffs,
        "workers": worker_items,
    }


def get_workers_stats(db: Session, telegram_id: str):
    owner = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not owner:
        return {"ok": False, "message": "Користувача не знайдено."}

    if owner.role != "owner":
        return {"ok": False, "message": "Тільки власник бачить працівників."}

    month_start, month_end = _month_range()

    workers = (
        db.query(User)
        .filter(User.role == "worker", User.is_active == True)
        .order_by(User.name.asc())
        .all()
    )

    items = []

    for worker in workers:
        shifts = (
            db.query(Shift)
            .filter(
                Shift.user_id == worker.id,
                Shift.started_at >= month_start,
                Shift.started_at < month_end,
            )
            .all()
        )
        shift_ids = [s.id for s in shifts]

        sales = []
        if shift_ids:
            sales = db.query(Sale).filter(Sale.shift_id.in_(shift_ids)).all()

        payouts = (
            db.query(Payout)
            .filter(
                Payout.user_id == worker.id,
                Payout.created_at >= month_start,
                Payout.created_at < month_end,
            )
            .all()
        )

        active_shift = (
            db.query(Shift)
            .filter(Shift.user_id == worker.id, Shift.status == "active")
            .first()
        )

        items.append(
            {
                "name": worker.name,
                "telegram_id": worker.telegram_id,
                "active_shift": active_shift is not None,
                "month_hooks": sum(s.quantity for s in sales),
                "month_revenue": sum(float(s.total_price) for s in sales),
                "month_payouts": sum(float(p.amount) for p in payouts),
            }
        )

    return {
        "ok": True,
        "items": items,
    }


def get_owner_payouts(db: Session, telegram_id: str):
    owner = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not owner:
        return {"ok": False, "message": "Користувача не знайдено."}

    if owner.role != "owner":
        return {"ok": False, "message": "Тільки власник бачить всі виплати."}

    payouts = db.query(Payout).order_by(Payout.id.desc()).all()

    items = []
    for p in payouts[:20]:
        worker = db.query(User).filter(User.id == p.user_id).first()
        items.append(
            {
                "worker_name": worker.name if worker else f"ID {p.user_id}",
                "amount": float(p.amount),
                "comment": p.comment or "-",
                "created_at": p.created_at.strftime("%d.%m.%Y %H:%M"),
            }
        )

    return {
        "ok": True,
        "total_amount": sum(float(p.amount) for p in payouts),
        "count": len(payouts),
        "items": items,
    }


def get_inventory_block(db: Session):
    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.is_active == True)
        .order_by(InventoryItem.name.asc())
        .all()
    )

    return [
        {
            "name": item.name,
            "grams_remaining": item.grams_remaining,
        }
        for item in items
    ]