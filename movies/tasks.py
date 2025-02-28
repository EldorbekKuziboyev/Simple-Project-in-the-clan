import asyncio
from celery import shared_task
from django.db import transaction
from movies.models import Movie
from aiogram import Bot
from aiogram.types import FSInputFile

# Данные бота
TOKEN = "7593798870:AAHKBUn8cKC8VaGQaanLbmRp2HVZB8UVbv4"
CHAT_ID = -1002359210651

bot = Bot(token=TOKEN)

async def send_video(video_path, caption):
    """Асинхронная отправка видео в Telegram"""
    video = FSInputFile(video_path)
    return await bot.send_video(chat_id=CHAT_ID, video=video, caption=caption or "🎬 Новый фильм!")

@shared_task(bind=True, max_retries=None)
def send_movie_to_channel(self, movie_id):
    """Celery-задача для отправки фильма в Telegram"""
    try:
        movie = Movie.objects.get(id=movie_id)
        if not movie.video_file:
            print("⚠️ Нет видеофайла для отправки.")
            return

        video_path = movie.video_file.path
        caption = f"🎬 {movie.title}" if movie.title else "🎬 Новый фильм!"

        # Запуск асинхронной функции в новом контексте
        message = asyncio.run(send_video(video_path, caption))

        if message and message.video:
            with transaction.atomic():
                movie.file_id = message.video.file_id
                movie.save()

    except Exception as e:
        print(f"❌ Ошибка при отправке видео: {e}")
        self.retry(exc=e, countdown=10)  # Повторная попытка через 60 секунд
