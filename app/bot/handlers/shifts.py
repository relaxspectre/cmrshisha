from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards.main import owner_menu, worker_menu
from app.bot.utils.live_dashboard import (
    build_shift_closed_report,
    build_worker_dashboard_text,
)
from app.core.database import SessionLocal
from app.models.user import User
from app.services.dashboard_service import get_worker_dashboard
from app.services.shift_service import start_shift, end_shift


def get_user_menu(user_role: str):
    if user_role == "owner":
        return owner_menu()
    return worker_menu()


async def start_shift_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"
        result = start_shift(db, telegram_id)
        dashboard = None
        if user_role == "worker" and result.get("ok"):
            dashboard = get_worker_dashboard(db, telegram_id)
    finally:
        db.close()

    if not user:
        await update.message.reply_text("Тебе немає в системі.")
        return

    await update.message.reply_text(
        f"✨ <b>{result['message']}</b>",
        reply_markup=get_user_menu(user_role),
        parse_mode="HTML"
    )

    if user_role == "worker" and result.get("ok") and dashboard and dashboard.get("ok"):
        await update.message.reply_text(
            build_worker_dashboard_text(dashboard),
            reply_markup=get_user_menu(user_role),
            parse_mode="HTML"
        )


async def end_shift_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"
        result = end_shift(db, telegram_id)
    finally:
        db.close()

    if not user:
        await update.message.reply_text("Тебе немає в системі.")
        return

    if result["ok"]:
        await update.message.reply_text(
            build_shift_closed_report(result),
            reply_markup=get_user_menu(user_role),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            result["message"],
            reply_markup=get_user_menu(user_role)
        )