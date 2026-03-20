from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.bot.keyboards.main import owner_menu, worker_menu
from app.core.database import SessionLocal
from app.models.user import User
from app.services.payout_service import add_payout, get_my_payouts, get_workers_list

PAYOUT_WORKER, PAYOUT_AMOUNT, PAYOUT_COMMENT = range(3)


def get_user_menu(user_role: str):
    if user_role == "owner":
        return owner_menu()
    return worker_menu()


async def my_payouts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"
        result = get_my_payouts(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=get_user_menu(user_role)
        )
        return

    if not result["items"]:
        text = "💵 У тебе поки немає виплат."
    else:
        lines = [
            "💵 Мої виплати",
            f"Загалом: {result['total_amount']} грн",
            f"Кількість виплат: {result['count']}",
            "",
            "Останні виплати:",
        ]

        for item in result["items"]:
            lines.append(
                f"• {item['created_at']} — {item['amount']} грн | {item['comment']}"
            )

        text = "\n".join(lines)

    await update.message.reply_text(
        text,
        reply_markup=get_user_menu(user_role)
    )


async def start_payout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            await update.message.reply_text("Тебе немає в системі.")
            return ConversationHandler.END

        if user.role != "owner":
            await update.message.reply_text(
                "Тільки власник може вносити виплати.",
                reply_markup=worker_menu()
            )
            return ConversationHandler.END

        workers = get_workers_list(db)
    finally:
        db.close()

    if not workers:
        await update.message.reply_text(
            "Немає активних працівників.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    keyboard = [[w["name"]] for w in workers]
    keyboard.append(["Скасувати"])

    context.user_data["workers_map"] = {
        w["name"]: w["telegram_id"] for w in workers
    }

    await update.message.reply_text(
        "Обери працівника:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return PAYOUT_WORKER


async def payout_worker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Скасувати":
        await update.message.reply_text(
            "Внесення виплати скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    workers_map = context.user_data.get("workers_map", {})

    if text not in workers_map:
        keyboard = [[name] for name in workers_map.keys()]
        keyboard.append(["Скасувати"])

        await update.message.reply_text(
            "Обери працівника кнопкою нижче:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return PAYOUT_WORKER

    context.user_data["payout_worker_name"] = text
    context.user_data["payout_worker_tg_id"] = workers_map[text]

    keyboard = [["Скасувати"]]
    await update.message.reply_text(
        "Введи суму виплати:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return PAYOUT_AMOUNT


async def payout_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Скасувати":
        await update.message.reply_text(
            "Внесення виплати скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    try:
        amount = float(text.replace(",", "."))
    except ValueError:
        keyboard = [["Скасувати"]]
        await update.message.reply_text(
            "Введи суму числом, наприклад: 500",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return PAYOUT_AMOUNT

    context.user_data["payout_amount"] = amount

    keyboard = [["Скасувати"]]
    await update.message.reply_text(
        "Введи коментар:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return PAYOUT_COMMENT


async def payout_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    owner_telegram_id = str(update.effective_user.id)

    if text == "Скасувати":
        await update.message.reply_text(
            "Внесення виплати скасовано.",
            reply_markup=owner_menu()
        )
        return ConversationHandler.END

    worker_tg_id = context.user_data["payout_worker_tg_id"]
    worker_name = context.user_data["payout_worker_name"]
    payout_amount_value = context.user_data["payout_amount"]

    db = SessionLocal()
    try:
        result = add_payout(
            db=db,
            owner_telegram_id=owner_telegram_id,
            worker_telegram_id=worker_tg_id,
            amount=payout_amount_value,
            comment=text,
        )
    finally:
        db.close()

    if result["ok"]:
        answer = (
            f"✅ Виплату додано\n"
            f"👤 Працівник: {result['worker_name']}\n"
            f"💰 Сума: {result['amount']} грн\n"
            f"📝 Коментар: {text}"
        )

        try:
            await context.bot.send_message(
                chat_id=int(worker_tg_id),
                text=(
                    f"💵 Тобі нараховано виплату\n\n"
                    f"💰 Сума: {result['amount']} грн\n"
                    f"📝 Коментар: {text}"
                )
            )
        except Exception:
            await update.message.reply_text(
                "⚠️ Виплату збережено, але повідомлення працівнику не доставлено.\n"
                "Ймовірно, він ще не натискав /start у боті.",
                reply_markup=owner_menu()
            )

    else:
        answer = result["message"]

    await update.message.reply_text(
        answer,
        reply_markup=owner_menu()
    )

    context.user_data.pop("workers_map", None)
    context.user_data.pop("payout_worker_name", None)
    context.user_data.pop("payout_worker_tg_id", None)
    context.user_data.pop("payout_amount", None)

    return ConversationHandler.END