from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.bot.keyboards.main import owner_menu
from app.core.database import SessionLocal
from app.models.user import User
from app.services.inventory_service import add_inventory_income, get_inventory_summary

INCOME_NAME, INCOME_GRAMS, INCOME_COMMENT = range(3)


async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = get_inventory_summary(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=owner_menu()
        )
        return

    if not result["items"]:
        text = "📦 Склад порожній."
    else:
        lines = [
            "📦 Склад",
            f"Загальний залишок: {result['total_grams']} г",
            "",
        ]

        for item in result["items"]:
            lines.append(f"• {item['name']} — {item['grams_remaining']} г")

        text = "\n".join(lines)

    await update.message.reply_text(
        text,
        reply_markup=owner_menu()
    )


async def start_inventory_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
    finally:
        db.close()

    if not user:
        await update.message.reply_text("Тебе немає в системі.")
        return ConversationHandler.END

    if user.role != "owner":
        await update.message.reply_text(
            "Тільки власник може додавати прихід.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Введи назву табаку:",
        reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
    )
    return INCOME_NAME


async def income_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Скасувати":
        await update.message.reply_text(
            "Додавання приходу скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    context.user_data["income_name"] = text

    await update.message.reply_text(
        "Введи кількість грам:",
        reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
    )
    return INCOME_GRAMS


async def income_grams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Скасувати":
        await update.message.reply_text(
            "Додавання приходу скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    try:
        grams = int(text)
    except ValueError:
        await update.message.reply_text(
            "Введи кількість грам числом.",
            reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
        )
        return INCOME_GRAMS

    context.user_data["income_grams"] = grams

    await update.message.reply_text(
        "Введи коментар:",
        reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
    )
    return INCOME_COMMENT


async def income_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)

    if text == "Скасувати":
        await update.message.reply_text(
            "Додавання приходу скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    db = SessionLocal()
    try:
        result = add_inventory_income(
            db=db,
            telegram_id=telegram_id,
            tobacco_name=context.user_data["income_name"],
            grams=context.user_data["income_grams"],
            comment=text,
        )
    finally:
        db.close()

    if result["ok"]:
        answer = (
            f"✅ Прихід додано\n"
            f"🌿 Табак: {result['item_name']}\n"
            f"📦 Новий залишок: {result['grams_remaining']} г"
        )
    else:
        answer = result["message"]

    await update.message.reply_text(
        answer,
        reply_markup=owner_menu()
    )

    context.user_data.pop("income_name", None)
    context.user_data.pop("income_grams", None)

    return ConversationHandler.END