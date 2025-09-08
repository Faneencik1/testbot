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
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

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

def main():
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Добавляем обработчик для всех типов сообщений
    application.add_handler(MessageHandler(filters.ALL, handle_all_messages))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
