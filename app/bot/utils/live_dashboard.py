from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards.main import worker_menu
from app.core.database import SessionLocal
from app.services.dashboard_service import get_worker_dashboard


WORKER_DASHBOARD_CHAT_KEY = "worker_dashboard_chat_id"
WORKER_DASHBOARD_MESSAGE_KEY = "worker_dashboard_message_id"


def _fmt_money(value) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else f"{value:.2f}"


def build_worker_dashboard_text(result: dict) -> str:
    shift = "🟢 <b>LOUNGE ACTIVE</b>" if result["shift_active"] else "⚪ <b>OFF SHIFT</b>"

    return (
        "━━━━━━━━━━━━━━━\n"
        "📊 <b>DARK LOUNGE DASHBOARD</b>\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"{shift}\n\n"
        "┌ 🔥 <b>ЗАРАЗ</b>\n"
        f"│ 💨 Кальяни: <b>{result['current_shift_hooks']}</b>\n"
        f"│ 💰 Виручка: <b>{_fmt_money(result['current_shift_revenue'])} грн</b>\n"
        f"│ 🌿 Списання: <b>{result['current_shift_writeoffs']}</b>\n"
        "└\n\n"
        "┌ 📅 <b>СЬОГОДНІ</b>\n"
        f"│ 💨 {result['today_hooks']} | 💰 {_fmt_money(result['today_revenue'])} грн\n"
        "└\n\n"
        "┌ 📆 <b>МІСЯЦЬ</b>\n"
        f"│ 💨 {result['month_hooks']} | 💰 {_fmt_money(result['month_revenue'])} грн\n"
        "└\n\n"
        f"💵 <b>Виплачено:</b> {_fmt_money(result['total_paid'])} грн\n"
        "\n✨ <i>Hookah flow in control</i>"
    )


def build_shift_closed_report(result: dict) -> str:
    return (
        "━━━━━━━━━━━━━━━\n"
        "🌙 <b>SHIFT CLOSED</b>\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"⏱ <b>Час зміни:</b> {result['duration_minutes']} хв\n"
        f"💨 <b>Кальяни:</b> {result['sales_count']}\n"
        f"💰 <b>Виручка:</b> {_fmt_money(result['revenue'])} грн\n"
        f"🌿 <b>Списання:</b> {result.get('writeoffs_count', 0)}\n\n"
        "🖤 <i>Зміна завершена. Дані збережено.</i>"
    )


async def open_worker_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = get_worker_dashboard(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=worker_menu()
        )
        return

    text = build_worker_dashboard_text(result)

    sent = await update.message.reply_text(
        text,
        reply_markup=worker_menu(),
        parse_mode="HTML"
    )

    context.user_data[WORKER_DASHBOARD_CHAT_KEY] = sent.chat_id
    context.user_data[WORKER_DASHBOARD_MESSAGE_KEY] = sent.message_id


async def refresh_worker_dashboard_if_exists(
    user_context_data: dict,
    bot,
    telegram_id: str,
):
    chat_id = user_context_data.get(WORKER_DASHBOARD_CHAT_KEY)
    message_id = user_context_data.get(WORKER_DASHBOARD_MESSAGE_KEY)

    if not chat_id or not message_id:
        return

    db = SessionLocal()
    try:
        result = get_worker_dashboard(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        return

    text = build_worker_dashboard_text(result)

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=worker_menu(),
            parse_mode="HTML"
        )
    except Exception:
        pass