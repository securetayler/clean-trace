import os
import logging
import requests
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Токен
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Нет токена! Проверь переменные окружения на Render.")

app = FastAPI()
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

    try:
        response = requests.get(
            f"https://xposedornot.com/api/check-email/{email}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            breaches = data.get("breaches", [])

            if not breaches:
                await update.message.reply_text(
                    f"✅ {email}\n\n"
                    "Утечек не найдено. Твой email чист."
                )
            else:
                breach_list = "\n".join([f"• {b}" for b in breaches[:10]])
                total = len(breaches)
                await update.message.reply_text(
                    f"⚠️ {email}\n\n"
                    f"Найдено утечек: {total}\n\n"
                    f"{breach_list}\n\n"
                    "Рекомендация: смени пароль на этих сервисах и включи 2FA."
                )
        else:
            await update.message.reply_text(
                f"Не удалось проверить {email}. Попробуй позже."
            )

    except Exception as e:
        await update.message.reply_text(
            f"Ошибка при проверке: {str(e)}"
        )

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_email))

@app.get("/")
async def index():
    return {"status": "ok"}

@app.post(f"/{TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return Response(content="ok", status_code=200)

@app.on_event("startup")
async def on_startup():
    public_url = os.environ.get("RENDER_EXTERNAL_URL")
    if public_url:
        await telegram_app.bot.set_webhook(f"{public_url}/{TOKEN}")
    await telegram_app.initialize()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
