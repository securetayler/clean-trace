import os
import logging
import hashlib
import requests
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Нет токена! Проверь переменные окружения на Render.")

app = FastAPI()
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡 *CleanTrace* — твой цифровой щит.\n\n"
        "Я проверяю, не утекли ли твои данные в открытый доступ.\n\n"
        "📧 *Проверка email*\n"
        "Отправь адрес — покажу, в каких утечках он засветился.\n\n"
        "🔑 *Проверка пароля*\n"
        "/password → отправь пароль → получишь количество утечек.\n\n"
        "📖 /help — подробная справка.\n"
        "ℹ️ /about — о боте и приватности.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔒 *Дисклеймер о конфиденциальности*\n\n"
        "_Мы не собираем и не храним адреса электронной почты, логины и номера телефонов, введённые в форму запроса в боте._\n\n"
        "_База данных утечек не хранится в боте. Мы получаем данные об утечках из публично доступных источников. Данные не верифицируются. Мы предоставляем их в том виде, в котором они были загружены в базу._\n\n"
        "_Наличие информации в результатах выдачи сервиса не является подтверждением факта утечки, равно как отсутствие информации по результатам запроса к сервису не является опровержением этого факта._\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📦 *Исходный код:*\n"
        "github.com/secretayler/clean-trace",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Как пользоваться CleanTrace*\n\n"
        "1️⃣ *Проверка email*\n"
        "Отправь боту email — получишь список утечек.\n\n"
        "2️⃣ *Проверка пароля*\n"
        "/password → отправь пароль → получишь количество утечек.\n\n"
        "3️⃣ *Команды*\n"
        "/start — начало работы\n"
        "/password — проверка пароля\n"
        "/help — эта справка\n"
        "/about — о боте\n\n"
        "🔒 _Все проверки анонимны. Пароли не передаются — только хеш._\n\n"
        "📦 github.com/secretayler/clean-trace",
        parse_mode="Markdown"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *О CleanTrace*\n\n"
        "Инструмент для аудита собственного цифрового следа. "
        "Проверяет email и пароли на наличие в публичных базах утечек.\n\n"
        "🔒 *Приватность*\n"
        "• Email не сохраняется — отправляется в открытый сервис XposedOrNot для проверки.\n"
        "• Пароли передаются только в виде хеша (SHA-1, k-anonymity). Сам пароль никуда не уходит.\n"
        "• Бот не ведёт логи пользователей и не хранит историю запросов.\n\n"
        "⚠️ *Дисклеймер*\n"
        "Данные об утечках получены из публичных источников и не верифицируются. "
        "Наличие или отсутствие информации не подтверждает и не опровергает факт утечки.\n\n"
        "📦 *Исходный код:*\n"
        "github.com/secretayler/clean-trace\n\n"
        "🛡 _Твои данные — твоё дело._",
        parse_mode="Markdown"
    )

async def password_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_password"] = True
    await update.message.reply_text(
        "Отправь пароль. Я проверю, светился ли он в утечках.\n\n"
        "⚠️ Сам пароль никуда не отправляется — только его хеш."
    )

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    if len(password) < 3:
        await update.message.reply_text("Слишком короткий пароль. Попробуй другой.")
        return

    await update.message.reply_text("Проверяю пароль...")

    try:
        sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]

        response = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            timeout=10
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"Не удалось проверить. Код ответа: {response.status_code}."
            )
            return

        hashes = response.text.splitlines()
        found = None
        for line in hashes:
            parts = line.split(":")
            if len(parts) == 2 and parts[0] == suffix:
                found = int(parts[1])
                break

        if found:
            await update.message.reply_text(
                f"⚠️ Этот пароль найден в утечках {found} раз.\n\n"
                "Смени его немедленно. Никогда не используй его снова."
            )
        else:
            await update.message.reply_text(
                "✅ Этот пароль в утечках не найден.\n\n"
                "Но помни: даже чистый пароль должен быть длинным (12+ символов)."
            )

    except Exception as e:
        await update.message.reply_text(f"Ошибка при проверке: {str(e)}")

async def check_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_password"):
        context.user_data["waiting_password"] = False
        await check_password(update, context)
        return

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
                    f"✅ {email}\n\nУтечек не найдено. Твой email чист."
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
        elif response.status_code == 404:
            await update.message.reply_text(
                f"✅ {email}\n\nУтечек не найдено. Твой email чист."
            )
        else:
            await update.message.reply_text(
                f"Не удалось проверить {email}. Код ответа: {response.status_code}."
            )

    except Exception as e:
        await update.message.reply_text(f"Ошибка при проверке: {str(e)}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("about", about_command))
telegram_app.add_handler(CommandHandler("password", password_command))
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
