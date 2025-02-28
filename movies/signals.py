import asyncio
from django.db.models.signals import post_save
from django.dispatch import receiver
from aiogram import Bot
from aiogram.types import FSInputFile
from movies.models import Movie

TOKEN = "7593798870:AAHKBUn8cKC8VaGQaanLbmRp2HVZB8UVbv4"
CHAT_ID = -1002359210651  # ID Telegram-канала
bot = Bot(token=TOKEN)


async def send_video(video_path, caption):
    video = FSInputFile(video_path)
    message = await bot.send_video(chat_id=CHAT_ID, video=video, caption=caption or "🎬 Новый фильм!")
    return message


@receiver(post_save, sender=Movie)
def send_movie_to_channel(sender, instance, created, **kwargs):
    """Сигнал отправляет видео в Telegram при сохранении нового фильма."""
    if created and instance.video_file:
        video_path = instance.video_file.path
        caption = f"🎬 {instance.title}" if instance.title else "🎬 Новый фильм!"

        # Запускаем асинхронную отправку видео
        asyncio.create_task(send_video(video_path, caption))
