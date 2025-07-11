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

async def is_admin(update: Update) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return update.effective_user.id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"Пользователь @{user.username} (ID: {user.id}) запустил бота.")
    await update.message.reply_text(
        "👋 Привет! Я могу пересылать:\n"
        "- Текстовые сообщения\n"
        "- Фотографии (включая альбомы)\n"
        "- Видео\n"
        "- Голосовые сообщения\n\n"
        "Просто отправь мне что-нибудь!"
    )

async def forward_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    caption = f"Медиа от @{user.username} (ID: {user.id})"
    
    try:
        # Обрабатываем медиагруппу (альбом)
        if update.message.media_group_id:
            if not context.user_data.get('processing_media_group'):
                context.user_data['processing_media_group'] = True
                context.user_data['media_group'] = []
                context.user_data['caption'] = update.message.caption or caption
            
            # Добавляем медиа в группу
            if update.message.photo:
                media = InputMediaPhoto(media=update.message.photo[-1].file_id)
            elif update.message.video:
                media = InputMediaVideo(media=update.message.video.file_id)
            
            if update.message.caption:
                context.user_data['caption'] = update.message.caption
            
            context.user_data['media_group'].append(media)
            return
            
        # Обрабатываем одиночные медиафайлы
        if update.message.photo:
            media = [InputMediaPhoto(media=update.message.photo[-1].file_id, 
                                  caption=update.message.caption or caption)]
        elif update.message.video:
            media = [InputMediaVideo(media=update.message.video.file_id, 
                                   caption=update.message.caption or caption)]
        elif update.message.voice:
            await context.bot.send_voice(
                chat_id=ADMIN_ID,
                voice=update.message.voice.file_id,
                caption=update.message.caption or caption
            )
            logger.info(f"Голосовое сообщение от @{user.username}")
            await update.message.reply_text("✅ Ваше голосовое сообщение переслано!")
            return

        # Отправляем медиагруппу
        if media:
            await context.bot.send_media_group(
                chat_id=ADMIN_ID,
                media=media
            )
            logger.info(f"Медиа от @{user.username} (ID: {user.id})")
            await update.message.reply_text("✅ Ваши медиафайлы пересланы!")

        # Очищаем данные медиагруппы после обработки
        if 'processing_media_group' in context.user_data:
            if len(context.user_data['media_group']) > 1:
                context.user_data['media_group'][0].caption = context.user_data['caption']
                await context.bot.send_media_group(
                    chat_id=ADMIN_ID,
                    media=context.user_data['media_group']
                )
            logger.info("Альбом из %d файлов от @%s", len(context.user_data['media_group']), user.username)
            
            context.user_data.pop('processing_media_group', None)
            context.user_data.pop('media_group', None)
            context.user_data.pop('caption', None)
            
    except Exception as e:
        logger.error(f"Ошибка пересылки медиа: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при пересылке медиа")

async def forward_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text

    logger.info(f"@{user.username} (ID: {user.id}): {text}")

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Сообщение от @{user.username} (ID: {user.id}):\n\n{text}"
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

        # Регистрируем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("getlog", get_log))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_text))
        app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE, forward_media_group))

        logger.info("🤖 Бот запущен!")
        app.run_polling(
            poll_interval=1.0,
            timeout=10,
            connect_timeout=5,
            pool_timeout=5,
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
