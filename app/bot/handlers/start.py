from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from app.bot.keyboards.main import owner_menu, worker_menu
from app.core.database import SessionLocal
from app.models.user import User


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    telegram_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "Telegram User"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            user = User(
                telegram_id=telegram_id,
                name=first_name,
                role="worker",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    finally:
        db.close()

    await update.message.reply_text(
        "Оновлюю меню...",
        reply_markup=ReplyKeyboardRemove(),
    )

    if user.role == "owner":
        await update.message.reply_text(
            f"Привіт, {user.name} 👑\nВідкрий панель кнопкою нижче.",
            reply_markup=owner_menu(),
        )
    else:
        await update.message.reply_text(
            f"Привіт, {user.name} 🔥\nВідкрий панель кнопкою нижче.",
            reply_markup=worker_menu(),
        )