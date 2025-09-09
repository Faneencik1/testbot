import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = "8018300330:AAEuB_STqH_5mAz8A6VPQqOJR4se4ZHI6m8"

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
    await update.message.reply_text(RESPONSE_TEXT)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.ALL, handle_all_messages))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
