import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Преобразуем в число

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие при /start."""
    await update.message.reply_text(
        "👋 Привет! Отправь мне сообщение, и я перешлю его создателю."
    )

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пересылает сообщение админу."""
    user = update.effective_user
    text = update.message.text

    if not text:
        await update.message.reply_text("❌ Поддерживаются только текстовые сообщения.")
        return

    # Форматируем сообщение для админа
    admin_msg = (
        f"📨 *Сообщение от* @{user.username} (ID: `{user.id}`):\n\n"
        f"{text}"
    )

    # Отправляем админу и подтверждаем пользователю
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_msg,
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Сообщение доставлено создателю!")

async def main() -> None:
    """Запуск бота."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin))

    # Запускаем бота
    print("🤖 Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
