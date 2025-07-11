import os
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("messages.log"),  # Запись в файл
        logging.StreamHandler()               # Вывод в консоль
    ]
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие при /start."""
    user = update.effective_user
    logger.info(f"Пользователь @{user.username} (ID: {user.id}) запустил бота.")
    await update.message.reply_text("👋 Привет! Отправь мне сообщение, и я перешлю его создателю.")

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пересылает сообщение админу и логирует его."""
    user = update.effective_user
    text = update.message.text

    if not text:
        await update.message.reply_text("❌ Поддерживаются только текстовые сообщения.")
        return

    # Логируем сообщение
    log_entry = f"@{user.username} (ID: {user.id}): {text}"
    logger.info(log_entry)

    # Пересылаем админу
    admin_msg = f"📨 *Сообщение от* @{user.username} (ID: `{user.id}`):\n\n{text}"
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
    logger.info("🤖 Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
