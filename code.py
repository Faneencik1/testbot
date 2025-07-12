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
        logging.FileHandler("bot.log"),
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
            if update.message.video_note:
                await self.send_video_note(update, context, user)
                return
            
            if update.message.media_group_id:
                await self.handle_media_group(update, context)
                return
            
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
        asyncio.create_task(self.send_media_group_delayed(media_group_id, context, update))

    async def send_media_group_delayed(self, media_group_id, context, update):
        await asyncio.sleep(3)
    
        async with self.lock:
            if media_group_id in self.media_groups:
                media_list, users = zip(*self.media_groups[media_group_id])
                user = users[0]
            
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"Альбом из {len(media_list)} медиа от @{user.username}"
                    )
                    await context.bot.send_media_group(
                        chat_id=ADMIN_ID,
                        media=list(media_list)
                    )
                    await update.message.reply_text("✅ Альбом переслан!")
                except Exception as e:
                    logger.error(f"Ошибка отправки альбома: {e}")
                finally:
                    del self.media_groups[media_group_id]

    async def send_video_note(self, update, context, user):
        try:
            await context.bot.send_video_note(
                chat_id=ADMIN_ID,
                video_note=update.message.video_note.file_id
            )
            await update.message.reply_text("✅ Видеосообщение переслано!")
        except Exception as e:
            logger.error(f"Ошибка пересылки видеосообщения: {e}")

    async def send_single_media(self, update, context, user):
        try:
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Бот активен! Отправьте медиа или текст.")

async def keep_alive(context: ContextTypes.DEFAULT_TYPE):
    """Фоновая задача для поддержания активности"""
    try:
        await context.bot.get_me()
        logger.info("Keep-alive: бот активен")
    except Exception as e:
        logger.error(f"Keep-alive ошибка: {e}")

async def forward_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Сообщение от @{update.effective_user.username}:\n{update.message.text}"
        )
        await update.message.reply_text("✅ Текст переслан!")
    except Exception as e:
        logger.error(f"Ошибка пересылки текста: {e}")

def main():
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем периодическую задачу (каждые 5 минут)
        app.job_queue.run_repeating(keep_alive, interval=300, first=10)
        
        # Обработчики команд
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_text))
        app.add_handler(MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE | filters.VOICE,
            media_manager.process_media
        ))

        logger.info("🟢 Бот запущен с keep-alive")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.critical(f"🔴 Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
