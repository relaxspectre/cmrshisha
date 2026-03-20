from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.bot.keyboards.main import owner_menu, worker_menu
from app.bot.utils.live_dashboard import build_worker_dashboard_text
from app.core.database import SessionLocal
from app.models.user import User
from app.services.dashboard_service import get_worker_dashboard
from app.services.inventory_service import get_inventory_items
from app.services.sale_service import add_sale

SELECT_TYPE, SELECT_TOBACCO, SELECT_QUANTITY = range(3)


def get_user_menu(user_role: str):
    if user_role == "owner":
        return owner_menu()
    return worker_menu()


async def start_add_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Premium (225)"],
        ["Hard (235)"],
        ["Скасувати"],
    ]

    await update.message.reply_text(
        "Обери тип кальяну:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return SELECT_TYPE


async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"

        if text == "Скасувати":
            await update.message.reply_text(
                "Скасовано.",
                reply_markup=get_user_menu(user_role)
            )
            return ConversationHandler.END

        if text == "Premium (225)":
            context.user_data["price"] = 225
            context.user_data["name"] = "Premium Hookah"
        elif text == "Hard (235)":
            context.user_data["price"] = 235
            context.user_data["name"] = "Hard Hookah"
        else:
            keyboard = [
                ["Premium (225)"],
                ["Hard (235)"],
                ["Скасувати"],
            ]
            await update.message.reply_text(
                "Обери тип кальяну кнопкою нижче:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return SELECT_TYPE

        items = get_inventory_items(db)
    finally:
        db.close()

    if not items:
        await update.message.reply_text(
            "Склад пустий. Спочатку додай прихід табаку.",
            reply_markup=get_user_menu(user_role)
        )
        return ConversationHandler.END

    keyboard = [[item["name"]] for item in items]
    keyboard.append(["Скасувати"])

    context.user_data["inventory_names"] = [item["name"] for item in items]

    await update.message.reply_text(
        "Обери табак:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return SELECT_TOBACCO


async def select_tobacco(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "Скасовано.",
            reply_markup=get_user_menu(user_role)
        )
        return ConversationHandler.END

    names = context.user_data.get("inventory_names", [])
    if text not in names:
        keyboard = [[name] for name in names]
        keyboard.append(["Скасувати"])
        await update.message.reply_text(
            "Обери табак кнопкою нижче:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return SELECT_TOBACCO

    context.user_data["tobacco_name"] = text

    await update.message.reply_text(
        "Введи кількість:",
        reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
    )

    return SELECT_QUANTITY


async def select_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"

        if text == "Скасувати":
            await update.message.reply_text(
                "Скасовано.",
                reply_markup=get_user_menu(user_role)
            )
            return ConversationHandler.END

        try:
            quantity = int(text)
        except ValueError:
            await update.message.reply_text(
                "Введи кількість числом, наприклад: 1",
                reply_markup=ReplyKeyboardMarkup([["Скасувати"]], resize_keyboard=True)
            )
            return SELECT_QUANTITY

        result = add_sale(
            db=db,
            telegram_id=telegram_id,
            product_name=context.user_data["name"],
            tobacco_name=context.user_data["tobacco_name"],
            quantity=quantity,
            unit_price=context.user_data["price"],
        )

        dashboard = None
        if user_role == "worker" and result.get("ok"):
            dashboard = get_worker_dashboard(db, telegram_id)
    finally:
        db.close()

    if not result.get("ok"):
        await update.message.reply_text(
            result.get("message", "Не вдалося додати продаж."),
            reply_markup=get_user_menu(user_role)
        )

        context.user_data.pop("price", None)
        context.user_data.pop("name", None)
        context.user_data.pop("tobacco_name", None)
        context.user_data.pop("inventory_names", None)

        return ConversationHandler.END

    await update.message.reply_text(
        f"✨ <b>ПРОДАЖ ДОДАНО</b>\n\n"
        f"💨 {context.user_data['name']}\n"
        f"🌿 {result['tobacco_name']}\n"
        f"🔢 {quantity}\n"
        f"💰 {result['total_price']} грн\n"
        f"📉 Автосписання: {result['grams_written_off']} г\n"
        f"📦 Залишок: {result['inventory_left']} г",
        reply_markup=get_user_menu(user_role),
        parse_mode="HTML"
    )

    if user_role == "worker" and dashboard and dashboard.get("ok"):
        await update.message.reply_text(
            build_worker_dashboard_text(dashboard),
            parse_mode="HTML",
            reply_markup=get_user_menu(user_role)
        )

    context.user_data.pop("price", None)
    context.user_data.pop("name", None)
    context.user_data.pop("tobacco_name", None)
    context.user_data.pop("inventory_names", None)

    return ConversationHandler.END