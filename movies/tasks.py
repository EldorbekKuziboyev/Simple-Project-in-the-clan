import asyncio
import os
import subprocess
from celery import shared_task
from django.db import transaction
from movies.models import Movie
from aiogram import Bot
from aiogram.types import FSInputFile
from django.core.exceptions import ObjectDoesNotExist

# Данные для бота
TOKEN = "7593798870:AAGCPzzkKBdBjHS_dY0851eoXjbuQ4AJ3Rs"
CHAT_ID = -1002359210651  # ID Telegram-канала
MAX_TG_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 ГБ
COMPRESSION_THRESHOLD = 50 * 1024 * 1024  # 50 МБ

def run_async(coro):
    """Создание нового event loop в каждом вызове"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def send_video(video_path, thumbnail_path, caption):
    """Асинхронная отправка видео в Telegram с миниатюрой"""
    bot = Bot(token=TOKEN)
    try:
        video = FSInputFile(video_path)
        thumbnail = FSInputFile(thumbnail_path) if thumbnail_path else None
        return await bot.send_video(
            chat_id=CHAT_ID,
            video=video,
            caption=caption or "🎬 Новый фильм!",
            thumbnail=thumbnail
        )
    finally:
        await bot.session.close()

async def send_video_by_file_id(file_id, caption):
    """Асинхронная отправка видео по file_id"""
    bot = Bot(token=TOKEN)
    try:
        return await bot.send_video(chat_id=CHAT_ID, video=file_id, caption=caption or "🎬 Новый фильм!")
    finally:
        await bot.session.close()

def get_file_size(file_path):
    """Получение размера файла в байтах"""
    return os.path.getsize(file_path) if os.path.exists(file_path) else 0

def compress_video(input_path):
    """Сжатие видео с помощью ffmpeg"""
    output_path = input_path.replace(".mp4", "_compressed.mp4")
    command = [
        "ffmpeg", "-i", input_path,
        "-vcodec", "libx264", "-crf", "28",
        "-preset", "fast", output_path,
        "-y"  # Перезаписывать файл
    ]
    subprocess.run(command, check=True)
    return output_path if os.path.exists(output_path) else None

@shared_task(bind=True, max_retries=None)
def send_movie_to_channel(self, movie_id):
    """Celery-задача для отправки фильма в Telegram, автоматически перезапускается"""
    try:
        movie = Movie.objects.get(id=movie_id)
    except ObjectDoesNotExist:
        print(f"⚠️ Фильм с ID {movie_id} не найден. Остановка задачи.")
        return

    caption = f"🎬 {movie.title}" if movie.title else "🎬 Новый фильм!"
    thumbnail_path = movie.thumbnail.path if movie.thumbnail else None

    if not movie.video_file:
        print("⚠️ Нет видеофайла для отправки.")
        return

    video_path = movie.video_file.path
    file_size = get_file_size(video_path)

    if file_size > MAX_TG_FILE_SIZE:
        print(f"❌ Файл {video_path} слишком большой ({file_size / (1024 * 1024)} МБ) для Telegram.")
        return

    if file_size > COMPRESSION_THRESHOLD:
        print(f"📉 Сжимаем видео {video_path}, так как оно больше {COMPRESSION_THRESHOLD / (1024 * 1024)} МБ...")
        compressed_path = compress_video(video_path)
        if compressed_path:
            video_path = compressed_path
            print(f"✅ Видео сжато: {video_path}")
        else:
            print("❌ Ошибка при сжатии видео.")
            return

    try:
        if movie.file_id:
            print("📤 Отправляем видео по file_id...")
            run_async(send_video_by_file_id(movie.file_id, caption))
        else:
            print("📤 Отправляем видеофайл...")
            message = run_async(send_video(video_path, thumbnail_path, caption))
            if message and message.video:
                with transaction.atomic():
                    movie.file_id = message.video.file_id
                    movie.save()
                    print(f"✅ Новый file_id сохранён: {movie.file_id}")
    except Exception as e:
        print(f"❌ Ошибка при отправке видео: {e}")
        send_movie_to_channel.apply_async(args=[movie_id], countdown=10)
