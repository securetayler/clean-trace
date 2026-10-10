import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токен из переменных окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Flask для Render
app = Flask(__name__)

# Telegram бот
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет. Я CleanTrace.\n"
        "Проверю твой email на утечки.\n\n"
        "Просто отправь мне свой email."
    )

async def check_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if "@" not in email:
        await update.message.reply_text("Это не похоже на email. Попробуй ещё раз.")
        return

    # Проверка через HIBP (публичный API для теста)
    # В реальности нужен ключ, но для демо используем заглушку
    await update.message.reply_text(f"Проверяю {email}...")

    # Заглушка — здесь будет реальный запрос к HIBP
    # Пока просто демонстрация работы
    await update.message.reply_text(
        f"Отчёт по {email}:\n\n"
        "Найдено утечек: 2\n"
        "1. LinkedIn (2012)\n"
        "2. Dropbox (2012)\n\n"
        "Рекомендация: смени пароль на этих сервисах и включи 2FA."
    )

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_email))

@app.route("/")
def index():
    return "CleanTrace bot is running."

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.process_update(update)
    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)