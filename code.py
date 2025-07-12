import os
import logging
import asyncio
from collections import defaultdict
from telegram import Update, InputMediaPhoto, InputMediaVideo
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

async def send_sender_info(context, user, media_type="сообщение"):
    """Отправляет информацию об отправителе отдельным сообщением"""
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Сообщение от @{user.username} (ID: {user.id}):"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        "👋 Привет! Я буду пересылать твои сообщения.\n"
        "Формат пересылки:\n"
        "1. Информация об отправителе\n"
        "2. Текст/медиа"
    )
    logger.info(f"Пользователь @{user.username} запустил бота")

async def forward_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text

    try:
        # Первое сообщение - информация об отправителе
        await send_sender_info(context, user)
        
        # Второе сообщение - текст
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text
        )
        
        await update.message.reply_text("✅ Ваше сообщение переслано!")
    except Exception as e:
        logger.error(f"Ошибка пересылки текста: {e}")

async def forward_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    try:
        await send_sender_info(context, user, "фото")
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=update.message.caption
        )
        await update.message.reply_text("✅ Фото переслано!")
    except Exception as e:
        logger.error(f"Ошибка пересылки фото: {e}")

async def forward_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    try:
        await send_sender_info(context, user, "видео")
        await context.bot.send_video(
            chat_id=ADMIN_ID,
            video=update.message.video.file_id,
            caption=update.message.caption
        )
        await update.message.reply_text("✅ Видео переслано!")
    except Exception as e:
        logger.error(f"Ошибка пересылки видео: {e}")

async def forward_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    try:
        await send_sender_info(context, user, "видеосообщение")
        await context.bot.send_video_note(
            chat_id=ADMIN_ID,
            video_note=update.message.video_note.file_id
        )
        await update.message.reply_text("✅ Видеосообщение переслано!")
    except Exception as e:
        logger.error(f"Ошибка пересылки видеосообщения: {e}")

async def forward_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    try:
        await send_sender_info(context, user, "голосовое сообщение")
        await context.bot.send_voice(
            chat_id=ADMIN_ID,
            voice=update.message.voice.file_id
        )
        await update.message.reply_text("✅ Голосовое сообщение переслано!")
    except Exception as e:
        logger.error(f"Ошибка пересылки голосового сообщения: {e}")

async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    try:
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=open("messages.log", "rb"),
            caption="📋 Логи бота"
        )
    except Exception as e:
        await update.message.reply_text("⚠️ Ошибка при отправке логов")
        logger.error(f"Ошибка отправки логов: {e}")

def main() -> None:
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Явно отключаем встроенный updater для избежания конфликтов
        app.updater = None
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("getlog", get_log))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_text))
        app.add_handler(MessageHandler(filters.PHOTO, forward_photo))
        app.add_handler(MessageHandler(filters.VIDEO, forward_video))
        app.add_handler(MessageHandler(filters.VIDEO_NOTE, forward_video_note))
        app.add_handler(MessageHandler(filters.VOICE, forward_voice))

        logger.info("🟢 Бот запущен")
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.critical(f"🔴 Ошибка запуска: {e}")
        raise

if __name__ == "__main__":
    main()
