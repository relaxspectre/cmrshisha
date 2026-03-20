from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards.main import owner_menu, worker_menu
from app.core.database import SessionLocal
from app.models.user import User
from app.services.dashboard_service import (
    get_cash_summary,
    get_owner_dashboard,
    get_owner_payouts,
    get_statistics_summary,
    get_worker_dashboard,
    get_workers_stats,
)


def get_user_menu(user_role: str):
    if user_role == "owner":
        return owner_menu()
    return worker_menu()


async def my_dashboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        user_role = user.role if user else "worker"
        result = get_worker_dashboard(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=get_user_menu(user_role)
        )
        return

    shift_status = "🟢 Активна" if result["shift_active"] else "⚪ Немає активної"

    text = (
        f"📊 Мій дашборд\n\n"
        f"Статус зміни: {shift_status}\n\n"
        f"За поточну зміну:\n"
        f"💨 Кальяни: {result['current_shift_hooks']}\n"
        f"💰 Виручка: {result['current_shift_revenue']} грн\n"
        f"🌿 Списання: {result['current_shift_writeoffs']}\n\n"
        f"За сьогодні:\n"
        f"💨 Кальяни: {result['today_hooks']}\n"
        f"💰 Виручка: {result['today_revenue']} грн\n\n"
        f"За місяць:\n"
        f"💨 Кальяни: {result['month_hooks']}\n"
        f"💰 Виручка: {result['month_revenue']} грн\n\n"
        f"💵 Виплачено всього: {result['total_paid']} грн"
    )

    await update.message.reply_text(
        text,
        reply_markup=get_user_menu(user_role)
    )


async def owner_dashboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = get_owner_dashboard(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=worker_menu()
        )
        return

    active_names = ", ".join(result["active_workers_names"]) if result["active_workers_names"] else "-"

    text = (
        f"📈 Дашборд власника\n\n"
        f"Сьогодні:\n"
        f"💨 Кальяни: {result['today_hooks']}\n"
        f"💰 Виручка: {result['today_revenue']} грн\n"
        f"📦 Собівартість: {result['today_cogs']} грн\n"
        f"📈 Валовий прибуток: {result['today_gross_profit']} грн\n"
        f"📉 Витрати: {result['today_expenses']} грн\n"
        f"💵 Виплати: {result['today_payouts']} грн\n"
        f"🧾 Чистий прибуток: {result['today_net_profit']} грн\n"
        f"🌿 Списання: {result['today_writeoffs']}\n\n"
        f"За місяць:\n"
        f"💨 Кальяни: {result['month_hooks']}\n"
        f"💰 Виручка: {result['month_revenue']} грн\n"
        f"📦 Собівартість: {result['month_cogs']} грн\n"
        f"📈 Валовий прибуток: {result['month_gross_profit']} грн\n"
        f"📉 Витрати: {result['month_expenses']} грн\n"
        f"💵 Виплати: {result['month_payouts']} грн\n"
        f"🧾 Чистий прибуток: {result['month_net_profit']} грн\n"
        f"🌿 Списання: {result['month_writeoffs']}\n\n"
        f"Активні працівники: {result['active_workers_count']}\n"
        f"👥 На зміні: {active_names}"
    )

    await update.message.reply_text(
        text,
        reply_markup=owner_menu()
    )


async def cash_summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = get_cash_summary(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=worker_menu()
        )
        return

    text = (
        f"💰 Каса\n\n"
        f"💨 Кальяни: {result['hooks']}\n"
        f"💵 Виручка: {result['revenue']} грн\n"
        f"📉 Витрати: {result['expenses']} грн\n"
        f"💸 Виплати: {result['payouts']} грн\n"
        f"🏦 Залишок: {result['cash']} грн"
    )

    await update.message.reply_text(
        text,
        reply_markup=owner_menu()
    )


async def statistics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = get_statistics_summary(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=worker_menu()
        )
        return

    lines = [
        "📊 Статистика",
        "",
        "За сьогодні:",
        f"💨 Кальяни: {result['today_hooks']}",
        f"💰 Виручка: {result['today_revenue']} грн",
        f"📦 Собівартість: {result['today_cogs']} грн",
        f"📈 Валовий прибуток: {result['today_gross_profit']} грн",
        f"📉 Витрати: {result['today_expenses']} грн",
        f"💵 Виплати: {result['today_payouts']} грн",
        f"🧾 Чистий прибуток: {result['today_net_profit']} грн",
        f"🌿 Списання: {result['today_writeoffs']}",
        "",
        "Минулий тиждень:",
        f"💨 Кальяни: {result['last_week_hooks']}",
        f"💰 Виручка: {result['last_week_revenue']} грн",
        f"📦 Собівартість: {result['last_week_cogs']} грн",
        f"📈 Валовий прибуток: {result['last_week_gross_profit']} грн",
        f"📉 Витрати: {result['last_week_expenses']} грн",
        f"💵 Виплати: {result['last_week_payouts']} грн",
        f"🧾 Чистий прибуток: {result['last_week_net_profit']} грн",
        f"🌿 Списання: {result['last_week_writeoffs']}",
        "",
        "За місяць:",
        f"💨 Кальяни: {result['month_hooks']}",
        f"💰 Виручка: {result['month_revenue']} грн",
        f"📦 Собівартість: {result['month_cogs']} грн",
        f"📈 Валовий прибуток: {result['month_gross_profit']} грн",
        f"📉 Витрати: {result['month_expenses']} грн",
        f"💵 Виплати: {result['month_payouts']} грн",
        f"🧾 Чистий прибуток: {result['month_net_profit']} грн",
        f"🌿 Списання: {result['month_writeoffs']}",
        "",
        "По працівниках:",
    ]

    if result["workers"]:
        for worker in result["workers"]:
            lines.append(
                f"• {worker['name']} — {worker['hooks']} кальянів — {worker['revenue']} грн"
            )
    else:
        lines.append("• Працівників поки немає")

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=owner_menu()
    )


async def workers_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = get_workers_stats(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=worker_menu()
        )
        return

    if not result["items"]:
        text = "👥 Працівників поки немає."
    else:
        lines = ["👥 Працівники", ""]
        for item in result["items"]:
            status = "🟢 На зміні" if item["active_shift"] else "⚪ Не на зміні"
            lines.append(
                f"{item['name']}\n"
                f"{status}\n"
                f"💨 Місяць: {item['month_hooks']}\n"
                f"💰 Виручка: {item['month_revenue']} грн\n"
                f"💵 Виплати: {item['month_payouts']} грн\n"
            )
        text = "\n".join(lines)

    await update.message.reply_text(
        text,
        reply_markup=owner_menu()
    )


async def owner_payouts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()
    try:
        result = get_owner_payouts(db, telegram_id)
    finally:
        db.close()

    if not result["ok"]:
        await update.message.reply_text(
            result["message"],
            reply_markup=worker_menu()
        )
        return

    if not result["items"]:
        text = "💸 Виплат поки немає."
    else:
        lines = [
            "💸 Виплати",
            f"Загальна сума: {result['total_amount']} грн",
            f"Кількість: {result['count']}",
            "",
            "Останні виплати:",
        ]

        for item in result["items"]:
            lines.append(
                f"• {item['created_at']} — {item['worker_name']} — {item['amount']} грн | {item['comment']}"
            )

        text = "\n".join(lines)

    await update.message.reply_text(
        text,
        reply_markup=owner_menu()
    )