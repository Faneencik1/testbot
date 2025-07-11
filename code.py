import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("messages.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

async def is_admin(update: Update) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return update.effective_user.id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"Пользователь @{user.username} (ID: {user.id}) запустил бота.")
    await update.message.reply_text("👋 Привет! Отправь мне сообщение, после чего оно появится в канале.")

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text

    if not text:
        await update.message.reply_text("❌ На данный момент поддерживаются только текстовые сообщения.")
        return

    logger.info(f"@{user.username} (ID: {user.id}): {text}")

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Сообщение от @{user.username} (ID: {user.id}):"
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text
        )
        await update.message.reply_text("✅ Ваше сообщение было переслано!")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")

async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет файл логов администратору"""
    if not await is_admin(update):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return

    try:
        with open("messages.log", "rb") as log_file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=log_file,
                caption="📄 Лог-файл бота"
            )
        logger.info(f"Администратор @{update.effective_user.username} запросил лог-файл")
    except FileNotFoundError:
        await update.message.reply_text("⚠️ Лог-файл не найден")
    except Exception as e:
        logger.error(f"Ошибка отправки лога: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при отправке лога")

def main() -> None:
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("getlog", get_log))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin))

        logger.info("🤖 Бот запущен!")
        app.run_polling(
            poll_interval=1.0,
            timeout=10,
            connect_timeout=5,
            pool_timeout=5
        )
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
