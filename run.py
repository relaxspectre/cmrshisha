from app.bot.bot import build_app

app = build_app()

print("Bot started...")
app.run_polling()