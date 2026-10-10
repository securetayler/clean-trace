import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Токен
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Нет токена! Проверь переменные окружения на Render.")

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

    await update.message.reply_text(f"Проверяю {email}...")

    # Заглушка для теста
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

def run_bot():
    # Запуск бота в фоне
    telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Flask на порту Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
