import asyncio
import os
import logging
from celery import shared_task
from django.db import transaction
from moviepy import VideoFileClip

from movies.models import Movie
from django.core.exceptions import ObjectDoesNotExist
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeVideo

logger = logging.getLogger(__name__)

API_ID = 24215300
API_HASH = "6ddc7ef111971e216873fb162d01bdfa"
CHAT_ID = -1002359210651
MAX_TG_FILE_SIZE = 2 * 1024 * 1024 * 1024
SESSION_NAME = "session_name"

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

def run_async(coro):
    """Использование текущего event loop без создания нового"""
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Ошибка в асинхронной функции: {e}")
        raise

async def start_client():
    """Запуск клиента Telethon"""
    if not client.is_connected():
        await client.start()

def get_video_metadata(video_path):
    clip = VideoFileClip(video_path)
    duration = clip.duration
    width, height = clip.size
    clip.close()
    return duration, width, height

async def send_video(video_path, caption):
    await client.start()
    duration, width, height = get_video_metadata(video_path)
    fixed_width = 1280
    fixed_height = 720
    attributes = [DocumentAttributeVideo(duration=duration, w=fixed_width, h=fixed_height)]
    return await client.send_file(
        CHAT_ID,
        video_path,
        caption=caption or "🎬 Новый фильм!",
        attributes=attributes,
        supports_streaming=True
    )


async def send_video_by_file_id(file_id, caption, video_path):
    """Отправка видео по file_id с использованием moviepy для получения метаданных"""
    await start_client()

    # Получаем метаданные видео
    duration, width, height = get_video_metadata(video_path)

    # Указываем атрибуты видео
    attributes = [DocumentAttributeVideo(duration=duration, w=width, h=height)]

    # Отправляем видео
    return await client.send_file(
        CHAT_ID,
        file=file_id,
        caption=caption or "🎬 Новый фильм!",
        attributes=attributes,
        supports_streaming=True
    )

def get_file_size(file_path):
    """Получение размера файла"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден.")
    return os.path.getsize(file_path)

@shared_task(bind=True, max_retries=3)
def send_movie_to_channel(self, movie_id):
    """Celery-задача отправки фильма в Telegram"""
    try:
        movie = Movie.objects.get(id=movie_id)
    except ObjectDoesNotExist:
        logger.error(f"⚠️ Фильм с ID {movie_id} не найден.")
        return

    caption = f"🎬 {movie.title_en}" if movie.title_en else "🎬 Новый фильм!"

    if not movie.video_file:
        logger.error("⚠️ Нет видеофайла для отправки.")
        return

    video_path = movie.video_file.path
    try:
        file_size = get_file_size(video_path)
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return

    if file_size > MAX_TG_FILE_SIZE:
        logger.error(f"❌ Файл {video_path} слишком большой ({file_size / (1024 * 1024)} МБ) для Telegram.")
        return

    try:
        if movie.file_id:
            logger.info("📤 Отправляем видео по file_id...")
            message = run_async(send_video_by_file_id(movie.file_id, caption))
        else:
            logger.info("📤 Отправляем видеофайл...")
            message = run_async(send_video(video_path, caption))

            if message and message.media:
                with transaction.atomic():
                    movie.file_id = message.id
                    movie.save()
                    logger.info(f"✅ Новый file_id сохранён: {movie.file_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке видео: {e}")
        self.retry(exc=e, countdown=10)