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

class MediaGroupManager:
    def __init__(self):
        self.media_groups = defaultdict(list)
        self.media_group_info = {}
        self.lock = asyncio.Lock()

    async def process_media_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        media_group_id = update.message.media_group_id

        async with self.lock:
            try:
                if media_group_id:
                    # Создаем медиа объект с учетом подписи
                    if update.message.photo:
                        media = InputMediaPhoto(
                            media=update.message.photo[-1].file_id,
                            caption=update.message.caption if update.message.caption else None
                        )
                    elif update.message.video:
                        media = InputMediaVideo(
                            media=update.message.video.file_id,
                            caption=update.message.caption if update.message.caption else None
                        )
                    else:
                        return

                    # Добавляем в группу и сохраняем информацию о первом сообщении
                    self.media_groups[media_group_id].append(media)
                    if media_group_id not in self.media_group_info:
                        self.media_group_info[media_group_id] = (user.username, user.id, update.message)
                    
                    # Запускаем отложенную отправку
                    asyncio.create_task(self.send_delayed_media_group(media_group_id, context))
                    return
                
                # Обработка одиночных медиа
                await self.send_single_media(update, context, user)
                
            except Exception as e:
                logger.error(f"Ошибка обработки медиа: {e}")

    async def send_delayed_media_group(self, media_group_id, context):
        await asyncio.sleep(3)  # Даем время для получения всех медиа в группе
        
        async with self.lock:
            if media_group_id in self.media_groups and media_group_id in self.media_group_info:
                media_list = self.media_groups.pop(media_group_id)
                username, user_id, first_message = self.media_group_info.pop(media_group_id)
                
                try:
                    # Первое сообщение - информация об отправителе
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"Альбом из {len(media_list)} медиа от @{username} (ID: {user_id}):"
                    )
                    
                    # Второе сообщение - весь альбом с сохранением подписей
                    await context.bot.send_media_group(
                        chat_id=ADMIN_ID,
                        media=media_list
                    )
                    
                    await first_message.reply_text("✅ Ваш альбом был переслан!")
                    logger.info(f"Отправлен альбом из {len(media_list)} медиа")
                except Exception as e:
                    logger.error(f"Ошибка отправки медиагруппы: {e}")

    async def send_single_media(self, update, context, user):
        try:
            # Первое сообщение - информация об отправителе
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"Медиа от @{user.username} (ID: {user.id}):"
            )

            # Второе сообщение - медиафайл с подписью (если есть)
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

# Глобальный менеджер медиагрупп
media_manager = MediaGroupManager()

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
    await media_manager.process_media_group(update, context)

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
