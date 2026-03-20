from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards.main import owner_menu
from app.core.database import SessionLocal
from app.services.admin_service import (
    delete_last_expense,
    delete_last_payout,
    delete_last_sale,
    delete_last_writeoff,
)


async def delete_last_sale_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = delete_last_sale(db, telegram_id)
    finally:
        db.close()

    await update.message.reply_text(
        result["message"],
        reply_markup=owner_menu()
    )


async def delete_last_expense_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = delete_last_expense(db, telegram_id)
    finally:
        db.close()

    await update.message.reply_text(
        result["message"],
        reply_markup=owner_menu()
    )


async def delete_last_payout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = delete_last_payout(db, telegram_id)
    finally:
        db.close()

    await update.message.reply_text(
        result["message"],
        reply_markup=owner_menu()
    )


async def delete_last_writeoff_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = delete_last_writeoff(db, telegram_id)
    finally:
        db.close()

    await update.message.reply_text(
        result["message"],
        reply_markup=owner_menu()
    )