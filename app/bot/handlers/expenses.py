from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.bot.keyboards.main import owner_menu
from app.core.database import SessionLocal
from app.models.user import User
from app.services.expense_service import add_expense

EXPENSE_CATEGORY, EXPENSE_AMOUNT, EXPENSE_COMMENT = range(3)


async def start_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else None
    finally:
        db.close()

    if not user:
        await update.message.reply_text("Тебе немає в системі.")
        return ConversationHandler.END

    if user_role != "owner":
        await update.message.reply_text("Тільки власник може вносити витрати.")
        return ConversationHandler.END

    keyboard = [
        ["Табак", "Вугілля"],
        ["Одноразки", "Напої"],
        ["Господарські", "Інше"],
        ["Скасувати"],
    ]

    await update.message.reply_text(
        "Обери категорію витрати:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return EXPENSE_CATEGORY


async def expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Скасувати":
        await update.message.reply_text(
            "Внесення витрати скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    context.user_data["expense_category"] = text

    keyboard = [["Скасувати"]]
    await update.message.reply_text(
        "Введи суму:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return EXPENSE_AMOUNT


async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Скасувати":
        await update.message.reply_text(
            "Внесення витрати скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    try:
        amount = float(text.replace(",", "."))
    except ValueError:
        keyboard = [["Скасувати"]]
        await update.message.reply_text(
            "Введи суму числом, наприклад: 850",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return EXPENSE_AMOUNT

    context.user_data["expense_amount"] = amount

    keyboard = [["Скасувати"]]
    await update.message.reply_text(
        "Введи коментар:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return EXPENSE_COMMENT


async def expense_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)

    if text == "Скасувати":
        await update.message.reply_text(
            "Внесення витрати скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    db = SessionLocal()
    try:
        result = add_expense(
            db=db,
            telegram_id=telegram_id,
            category=context.user_data["expense_category"],
            amount=context.user_data["expense_amount"],
            comment=text,
        )
    finally:
        db.close()

    if result["ok"]:
        answer = (
            f"✅ Витрату додано\n"
            f"📂 Категорія: {context.user_data['expense_category']}\n"
            f"💰 Сума: {result['amount']} грн\n"
            f"📝 Коментар: {text}"
        )
    else:
        answer = result["message"]

    await update.message.reply_text(
        answer,
        reply_markup=owner_menu()
    )

    context.user_data.pop("expense_category", None)
    context.user_data.pop("expense_amount", None)

    return ConversationHandler.END