import os
import logging
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"Пользователь @{user.username} (ID: {user.id}) запустил бота.")
    await update.message.reply_text(
        "👋 Привет! Я могу пересылать:\n"
        "- Текстовые сообщения\n"
        "- Фото (включая альбомы)\n"
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
        # Для медиагрупп (альбомов)
        if update.message.media_group_id:
            if 'media_group' not in context.user_data:
                context.user_data['media_group'] = []
                context.user_data['media_group_id'] = update.message.media_group_id
                context.user_data['sender_info'] = f"Альбом от @{user.username} (ID: {user.id}):"
            
            # Добавляем медиа в группу
            if update.message.photo:
                media = InputMediaPhoto(media=update.message.photo[-1].file_id)
            elif update.message.video:
                media = InputMediaVideo(media=update.message.video.file_id)
            
            context.user_data['media_group'].append(media)
            return
        
        # Первое сообщение - информация об отправителе
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Медиа от @{user.username} (ID: {user.id}):"
        )

        # Второе сообщение - медиафайл
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=update.message.photo[-1].file_id,
                caption=update.message.caption
            )
        elif update.message.video:
            await context.bot.send_video(
                chat_id=ADMIN_ID,
                video=update.message.video.file_id,
                caption=update.message.caption
            )
        elif update.message.voice:
            await context.bot.send_voice(
                chat_id=ADMIN_ID,
                voice=update.message.voice.file_id
            )
            
        await update.message.reply_text("✅ Ваше медиа было переслано!")
    except Exception as e:
        logger.error(f"Ошибка пересылки медиа: {e}")

async def handle_media_group(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка собранных медиагрупп"""
    try:
        if 'media_group' in context.user_data and len(context.user_data['media_group']) > 0:
            # Первое сообщение - информация об отправителе
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=context.user_data['sender_info']
            )
            
            # Второе сообщение - весь альбом
            await context.bot.send_media_group(
                chat_id=ADMIN_ID,
                media=context.user_data['media_group']
            )
            
            # Очищаем данные
            context.user_data.pop('media_group', None)
            context.user_data.pop('media_group_id', None)
            context.user_data.pop('sender_info', None)
    except Exception as e:
        logger.error(f"Ошибка обработки медиагруппы: {e}")

def main() -> None:
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        # Регистрируем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_text))
        app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE, forward_media))
        
        # Обработчик для завершения медиагрупп
        app.job_queue.run_repeating(handle_media_group, interval=5.0)

        logger.info("🤖 Бот запущен!")
        app.run_polling()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
