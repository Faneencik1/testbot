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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"Пользователь @{user.username} (ID: {user.id}) запустил бота.")
    await update.message.reply_text(
        "👋 Привет! Я могу пересылать:\n"
        "- Текстовые сообщения\n"
        "- Фотографии\n"
        "- Видео\n"
        "- Голосовые сообщения\n\n"
        "Просто отправь мне что-нибудь!"
    )

async def forward_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text

    logger.info(f"@{user.username} (ID: {user.id}): {text}")

    try:
        # Первое сообщение - информация об отправителе
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Сообщение от @{user.username} (ID: {user.id}):"
        )
        
        # Второе сообщение - текст
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text
        )
        
        await update.message.reply_text("✅ Ваше сообщение было переслано!")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")

async def forward_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    try:
        # Первое сообщение - информация об отправителе
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Медиафайл от @{user.username} (ID: {user.id}):"
        )

        # Второе сообщение - сам медиафайл
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=update.message.photo[-1].file_id,
                caption=f"Фото от @{user.username} (ID: {user.id})"
            )
        elif update.message.video:
            await context.bot.send_video(
                chat_id=ADMIN_ID,
                video=update.message.video.file_id,
                caption=f"Видео от @{user.username} (ID: {user.id})"
            )
        elif update.message.voice:
            # Голосовое сообщение без подписи
            await context.bot.send_voice(
                chat_id=ADMIN_ID,
                voice=update.message.voice.file_id
            )
            
        await update.message.reply_text("✅ Ваше медиа было переслано!")
    except Exception as e:
        logger.error(f"Ошибка пересылки медиа: {e}")

def main() -> None:
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        # Регистрируем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_text))
        app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE, forward_media))

        logger.info("🤖 Бот запущен!")
        app.run_polling()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
