import os

from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.handlers.admin import (
    delete_last_expense_handler,
    delete_last_payout_handler,
    delete_last_sale_handler,
    delete_last_writeoff_handler,
)
from app.bot.handlers.dashboard import (
    cash_summary_handler,
    my_dashboard_handler,
    owner_dashboard_handler,
    owner_payouts_handler,
    statistics_handler,
    workers_handler,
)
from app.bot.handlers.expenses import (
    start_expense,
    expense_category,
    expense_amount,
    expense_comment,
    EXPENSE_CATEGORY,
    EXPENSE_AMOUNT,
    EXPENSE_COMMENT,
)
from app.bot.handlers.inventory import (
    inventory_handler,
    start_inventory_income,
    income_name,
    income_grams,
    income_comment,
    INCOME_NAME,
    INCOME_GRAMS,
    INCOME_COMMENT,
)
from app.bot.handlers.payouts import (
    my_payouts_handler,
    start_payout,
    payout_worker,
    payout_amount,
    payout_comment,
    PAYOUT_WORKER,
    PAYOUT_AMOUNT,
    PAYOUT_COMMENT,
)
from app.bot.handlers.sales import (
    start_add_sale,
    select_type,
    select_tobacco,
    select_quantity,
    SELECT_TYPE,
    SELECT_TOBACCO,
    SELECT_QUANTITY,
)
from app.bot.handlers.shifts import start_shift_handler, end_shift_handler
from app.bot.handlers.start import start_command
from app.bot.handlers.writeoffs import (
    start_writeoff,
    writeoff_name,
    writeoff_quantity,
    writeoff_comment,
    WRITEOFF_NAME,
    WRITEOFF_QTY,
    WRITEOFF_COMMENT,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    sale_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Додати продаж$"), start_add_sale)
        ],
        states={
            SELECT_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_type)
            ],
            SELECT_TOBACCO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_tobacco)
            ],
            SELECT_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_quantity)
            ],
        },
        fallbacks=[],
    )

    writeoff_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Списання табаку$"), start_writeoff)
        ],
        states={
            WRITEOFF_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, writeoff_name)
            ],
            WRITEOFF_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, writeoff_quantity)
            ],
            WRITEOFF_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, writeoff_comment)
            ],
        },
        fallbacks=[],
    )

    expense_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Внести витрату$"), start_expense)
        ],
        states={
            EXPENSE_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_category)
            ],
            EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)
            ],
            EXPENSE_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_comment)
            ],
        },
        fallbacks=[],
    )

    payout_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Внести виплату$"), start_payout)
        ],
        states={
            PAYOUT_WORKER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, payout_worker)
            ],
            PAYOUT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, payout_amount)
            ],
            PAYOUT_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, payout_comment)
            ],
        },
        fallbacks=[],
    )

    inventory_income_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Додати прихід$"), start_inventory_income)
        ],
        states={
            INCOME_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, income_name)
            ],
            INCOME_GRAMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, income_grams)
            ],
            INCOME_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, income_comment)
            ],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.Regex("^Почати зміну$"), start_shift_handler))
    app.add_handler(sale_conv)
    app.add_handler(writeoff_conv)
    app.add_handler(expense_conv)
    app.add_handler(payout_conv)
    app.add_handler(inventory_income_conv)
    app.add_handler(MessageHandler(filters.Regex("^Мій дашборд$"), my_dashboard_handler))
    app.add_handler(MessageHandler(filters.Regex("^Мої виплати$"), my_payouts_handler))
    app.add_handler(MessageHandler(filters.Regex("^Дашборд$"), owner_dashboard_handler))
    app.add_handler(MessageHandler(filters.Regex("^Каса$"), cash_summary_handler))
    app.add_handler(MessageHandler(filters.Regex("^Статистика$"), statistics_handler))
    app.add_handler(MessageHandler(filters.Regex("^Працівники$"), workers_handler))
    app.add_handler(MessageHandler(filters.Regex("^Виплати$"), owner_payouts_handler))
    app.add_handler(MessageHandler(filters.Regex("^Склад$"), inventory_handler))
    app.add_handler(MessageHandler(filters.Regex("^Видалити останній продаж$"), delete_last_sale_handler))
    app.add_handler(MessageHandler(filters.Regex("^Видалити останню витрату$"), delete_last_expense_handler))
    app.add_handler(MessageHandler(filters.Regex("^Видалити останню виплату$"), delete_last_payout_handler))
    app.add_handler(MessageHandler(filters.Regex("^Видалити останнє списання$"), delete_last_writeoff_handler))
    app.add_handler(MessageHandler(filters.Regex("^Закрити зміну$"), end_shift_handler))

    return app