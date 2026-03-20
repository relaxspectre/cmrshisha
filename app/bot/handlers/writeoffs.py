from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.bot.keyboards.main import owner_menu, worker_menu
from app.bot.utils.live_dashboard import refresh_worker_dashboard_if_exists
from app.core.database import SessionLocal
from app.models.user import User
from app.services.inventory_service import get_inventory_items
from app.services.writeoff_service import add_writeoff

WRITEOFF_NAME, WRITEOFF_QTY, WRITEOFF_COMMENT = range(3)


def get_user_menu(user_role: str):
    if user_role == "owner":
        return owner_menu()
    return worker_menu()


async def start_writeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        items = get_inventory_items(db)
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"
    finally:
        db.close()

    if not items:
        await update.message.reply_text(
            "На складі немає табаку для списання.",
            reply_markup=get_user_menu(user_role)
        )
        return ConversationHandler.END

    keyboard = [[item["name"]] for item in items]
    keyboard.append(["Скасувати"])

    context.user_data["writeoff_inventory_names"] = [item["name"] for item in items]

    await update.message.reply_text(
        "Вибери табак:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return WRITEOFF_NAME


async def writeoff_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"
    finally:
        db.close()

    if text == "Скасувати":
        await update.message.reply_text(
            "Списання скасовано.",
            reply_markup=get_user_menu(user_role)
        )
        return ConversationHandler.END

    names = context.user_data.get("writeoff_inventory_names", [])
    if text not in names:
        keyboard = [[name] for name in names]
        keyboard.append(["Скасувати"])
        await update.message.reply_text(
            "Вибери табак кнопкою нижче:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return WRITEOFF_NAME

    context.user_data["writeoff_name"] = text

    await update.message.reply_text(
        "Введи кількість грам:",
        reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
    )
    return WRITEOFF_QTY


async def writeoff_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"
    finally:
        db.close()

    if text == "Скасувати":
        await update.message.reply_text(
            "Списання скасовано.",
            reply_markup=get_user_menu(user_role)
        )
        return ConversationHandler.END

    try:
        quantity = int(text)
    except ValueError:
        await update.message.reply_text(
            "Введи кількість числом.",
            reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
        )
        return WRITEOFF_QTY

    context.user_data["writeoff_qty"] = quantity

    await update.message.reply_text(
        "Введи коментар:",
        reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
    )
    return WRITEOFF_COMMENT


async def writeoff_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"

        if text == "Скасувати":
            await update.message.reply_text(
                "Списання скасовано.",
                reply_markup=get_user_menu(user_role)
            )
            return ConversationHandler.END

        result = add_writeoff(
            db=db,
            telegram_id=telegram_id,
            tobacco_name=context.user_data["writeoff_name"],
            quantity=context.user_data["writeoff_qty"],
            comment=text,
        )
    finally:
        db.close()

    if result["ok"]:
        answer = (
            f"✅ Списання збережено\n"
            f"🌿 Табак: {context.user_data['writeoff_name']}\n"
            f"🔢 Кількість: {context.user_data['writeoff_qty']} г\n"
            f"📝 Коментар: {text}\n"
            f"📦 Залишок: {result['grams_left']} г"
        )
    else:
        answer = result["message"]

    await update.message.reply_text(
        answer,
        reply_markup=get_user_menu(user_role)
    )

    if user_role == "worker" and result.get("ok"):
        await refresh_worker_dashboard_if_exists(
            user_context_data=context.user_data,
            bot=context.bot,
            telegram_id=telegram_id,
        )

    context.user_data.pop("writeoff_name", None)
    context.user_data.pop("writeoff_qty", None)
    context.user_data.pop("writeoff_inventory_names", None)

    return ConversationHandler.END