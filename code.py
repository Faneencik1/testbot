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
        self.lock = asyncio.Lock()

    async def process_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        try:
            # Видеосообщения (кружки)
            if update.message.video_note:
                await self.send_video_note(update, context, user)
                return
            
            # Медиагруппы (альбомы)
            if update.message.media_group_id:
                await self.handle_media_group(update, context)
                return
            
            # Одиночные медиа
            await self.send_single_media(update, context, user)
            
        except Exception as e:
            logger.error(f"Ошибка обработки медиа: {e}")

    async def handle_media_group(self, update, context):
        user = update.effective_user
        media_group_id = update.message.media_group_id
        
        async with self.lock:
            if update.message.photo:
                media = InputMediaPhoto(
                    media=update.message.photo[-1].file_id,
                    caption=update.message.caption
                )
            elif update.message.video:
                media = InputMediaVideo(
                    media=update.message.video.file_id,
                    caption=update.message.caption
                )
            else:
                return

            self.media_groups[media_group_id].append((media, user))
            asyncio.create_task(self.send_media_group_delayed(media_group_id, context))

    async def send_media_group_delayed(self, media_group_id, context):
        await asyncio.sleep(3)  # Ожидание сбора всех медиа
        
        async with self.lock:
            if media_group_id in self.media_groups:
                media_list, users = zip(*self.media_groups[media_group_id])
                user = users[0]
                
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"Альбом из {len(media_list)} медиа от @{user.username} (ID: {user.id}):"
                    )
                    await context.bot.send_media_group(
                        chat_id=ADMIN_ID,
                        media=list(media_list)
                    )
                    logger.info(f"Отправлен альбом из {len(media_list)} медиа")
                except Exception as e:
                    logger.error(f"Ошибка отправки альбома: {e}")
                finally:
                    del self.media_groups[media_group_id]

    async def send_video_note(self, update, context, user):
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"Видеосообщение от @{user.username} (ID: {user.id}):"
            )
            await context.bot.send_video_note(
                chat_id=ADMIN_ID,
                video_note=update.message.video_note.file_id
            )
            await update.message.reply_text("✅ Видеосообщение переслано!")
        except Exception as e:
            logger.error(f"Ошибка пересылки видеосообщения: {e}")

    async def send_single_media(self, update, context, user):
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"Медиа от @{user.username} (ID: {user.id}):"
            )

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
                
            await update.message.reply_text("✅ Медиа переслано!")
        except Exception as e:
            logger.error(f"Ошибка пересылки медиа: {e}")

media_manager = MediaGroupManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        "👋 Бот работает! Отправьте:\n"
        "- Текст\n- Фото/Видео\n- Видеосообщения\n- Голосовые"
    )
    logger.info(f"Пользователь @{user.username} запустил бота")

async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    try:
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=open("messages.log", "rb"),
            caption="📋 Логи бота"
        )
        logger.info(f"Админ @{user.username} запросил логи")
    except Exception as e:
        logger.error(f"Ошибка отправки логов: {e}")
        await update.message.reply_text("⚠️ Ошибка при отправке логов")

async def forward_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Сообщение от @{user.username} (ID: {user.id}):\n\n{text}"
        )
        await update.message.reply_text("✅ Сообщение переслано!")
    except Exception as e:
        logger.error(f"Ошибка пересылки текста: {e}")

def main() -> None:
    # Убедитесь, что только один экземпляр бота запущен
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Явно отключаем встроенный updater для избежания конфликтов
        app.updater = None
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("getlog", get_log))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_text))
        app.add_handler(MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE | filters.VOICE,
            media_manager.process_media
        ))

        logger.info("🟢 Бот запущен (без updater)")
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.critical(f"🔴 Ошибка запуска: {e}")
        raise

if __name__ == "__main__":
    main()
