import requests

async def check_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if "@" not in email:
        await update.message.reply_text("Это не похоже на email. Попробуй ещё раз.")
        return

    await update.message.reply_text(f"Проверяю {email}...")

    try:
        # Запрос к XposedOrNot API
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
