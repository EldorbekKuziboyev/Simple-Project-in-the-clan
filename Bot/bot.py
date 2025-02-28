import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "7593798870:AAHKBUn8cKC8VaGQaanLbmRp2HVZB8UVbv4"
API_URL = "https://640c-86-62-2-249.ngrok-free.app/api/movies/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🎬 Привет! Отправь /movies, чтобы получить список фильмов.")

@dp.message(Command("movies"))
async def get_movies(message: types.Message):
    response = requests.get(API_URL)
    if response.status_code == 200:
        movies = response.json()
        if not movies:
            await message.answer("🎞️ Пока фильмов нет.")
            return

        text = "🎬 Доступные фильмы:\n\n"
        for movie in movies:
            text += f"📽️ {movie['title']}\n➡️ /download_{movie['id']}\n\n"

        await message.answer(text, parse_mode="HTML")
    else:
        await message.answer("❌ Ошибка при получении списка фильмов.")

@dp.message(lambda message: message.text.startswith("/download_"))
async def download_movie(message: types.Message):
    movie_id = message.text.split("_")[1]
    movie_url = f"{API_URL}{movie_id}/download/"

    response = requests.get(movie_url)
    if response.status_code == 200:
        movie_data = response.json()
        if "file_id" in movie_data:
            await message.answer_video(movie_data["file_id"])
        else:
            await message.answer("❌ Фильм еще не загружен в Telegram.")
    else:
        await message.answer("❌ Не удалось найти фильм.")

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
