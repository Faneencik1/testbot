import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота (получите у @BotFather)
BOT_TOKEN = "8018300330:AAEuB_STqH_5mAz8A6VPQqOJR4se4ZHI6m8"
PORT = int(os.environ.get('PORT', 5000)) 
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Текст ответа
RESPONSE_TEXT = (
    "Привет! Канал «ОТБРОСЫ СЕВСКА2» был продан, поэтому бот стал недействительным. "
    "Чтобы отправить сообщение в канал, напишите сюда — @kostrovvv29.\n\n"
    "Поддержка этого бота будет прекращена 16 сентября в 20:00."
)

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RESPONSE_TEXT)

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RESPONSE_TEXT)

# Обработчик всех типов сообщений
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    message_type = update.message.content_type
    
    logger.info(f"Пользователь {user_name} отправил сообщение типа: {message_type}")
    
    # Отправляем стандартный ответ
    await update.message.reply_text(RESPONSE_TEXT)

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка при обработке сообщения: {context.error}")

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getlog", get_log))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE, forward_media_group))

    # Определяем режим работы
    if WEBHOOK_URL and os.environ.get('RENDER'):
        logger.info("🚀 Запуск в режиме webhook (Render)")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )
    else:
        logger.info("🔄 Запуск в режиме polling (локально)")
        app.run_polling(
            poll_interval=1.0,
            timeout=10,
            allowed_updates=Update.ALL_TYPES
        )

if __name__ == "__main__":
    main()
