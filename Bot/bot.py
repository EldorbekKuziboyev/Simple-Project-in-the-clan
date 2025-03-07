import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "7593798870:AAGCPzzkKBdBjHS_dY0851eoXjbuQ4AJ3Rs"
API_URL = "https://8385-86-62-2-249.ngrok-free.app/api/movies/"



bot = Bot(token=TOKEN)
dp = Dispatcher()

MOVIES_PER_PAGE = 5


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🎬 Привет! Отправь /movies, чтобы получить список фильмов.")


@dp.message(Command("movies"))
async def get_movies(message: types.Message, page: int = 0):
    await paginate(message, page)


async def paginate(target: types.Message | types.CallbackQuery, page: int):
    response = requests.get(API_URL)

    if response.status_code == 200:
        movies = response.json()

        if not movies:
            if isinstance(target, types.Message):
                await target.answer("🎞️ Пока фильмов нет.")
            else:
                await target.answer("🎞️ Пока фильмов нет.", show_alert=True)
            return

        start_idx = page * MOVIES_PER_PAGE
        end_idx = start_idx + MOVIES_PER_PAGE
        paginated_movies = movies[start_idx:end_idx]
        keyboard = InlineKeyboardBuilder()
        text = "🎬 Доступные фильмы:\n\n"
        for idx, movie in enumerate(paginated_movies, start=1):
            text += f"{idx}.📽️ {movie['title']}\n"
            keyboard.button(text=str(idx), callback_data=f"download_{movie['id']}")

        keyboard.adjust(3)


        if page > 0:
            keyboard.button(text="⬅️ Назад", callback_data=f"movies_{page - 1}")

        if end_idx < len(movies):
            keyboard.button(text="➡️ Вперед", callback_data=f"movies_{page + 1}")

        if isinstance(target, types.Message):
            await target.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        else:
            await target.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            await target.answer()
    else:
        await target.answer("❌ Ошибка при получении списка фильмов.")


@dp.callback_query(lambda callback: callback.data.startswith("movies_"))
async def paginate_movies(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[1])
    await paginate(callback, page)

async def get_channels():
    """Запрос списка каналов из API"""
    response = requests.get(f"{API_URL}channels/")
    if response.status_code == 200:
        return response.json()
    return {}

@dp.callback_query(lambda call: call.data.startswith("download_"))
async def download_movie(call: types.CallbackQuery):
    movie_id = call.data.split("_")[1]
    movie_url = f"{API_URL}{movie_id}/download/"

    response = requests.get(movie_url)
    user_id = call.from_user.id

    channels = await get_channels()  # Получаем актуальный список каналов
    not_subscribed = []

    for chat_id, link in channels.items():
        user_status = await bot.get_chat_member(chat_id=int(chat_id), user_id=user_id)
        if user_status.status not in ["member", "administrator", "creator"]:
            not_subscribed.append((chat_id, link))

    if not not_subscribed:
        if response.status_code == 200:
            movie_data = response.json()
            if "file_id" in movie_data:
                await call.message.answer_video(
                    movie_data["file_id"],
                    caption=f"{movie_data['title']}\nЖанр: {', '.join(movie_data['type'])}\n"
                            f"Оценки: {movie_data['stars']}\nГод выпуска: {movie_data['film_year_manufacture'][:4]}",
                    protect_content=True
                )
            else:
                await call.message.answer("❌ Фильм еще не загружен в Telegram.")
        else:
            await call.message.answer("❌ Не удалось найти фильм.")
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"🔗 Подписаться на канал {i+1}", url=link)]
                for i, (chat_id, link) in enumerate(not_subscribed)
            ] + [[InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]]
        )

        await call.message.answer(
            "Вы еще не подписались! Подпишитесь на все каналы и нажмите кнопку проверки.",
            reply_markup=keyboard
        )

@dp.callback_query(lambda call: call.data == "check_sub")
async def check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id
    channels = await get_channels()

    not_subscribed = []
    for chat_id, link in channels.items():
        user_status = await bot.get_chat_member(chat_id=int(chat_id), user_id=user_id)
        if user_status.status not in ["member", "administrator", "creator"]:
            not_subscribed.append((chat_id, link))

    if not not_subscribed:
        await call.message.edit_text("✅ Вы подписаны на все каналы!")
    else:
        await call.answer("❌ Вы все еще не подписаны на все каналы!", show_alert=True)


@dp.message(Command("search"))
async def search_movies(message: types.Message):
    query = message.text.replace("/search ", "").strip()
    if not query:
        await message.answer("🔎 Использование: `/search название фильма`", parse_mode="Markdown")
        return

    search_url = f"{API_URL}search/{query}/"
    response = requests.get(search_url)

    if response.status_code == 200:
        movies = response.json().get("results", [])
        if not movies:
            await message.answer("❌ Фильмы не найдены.")
            return

        await send_paginated_search_results(message, movies, query, 0)
    else:
        await message.answer("❌ Ошибка при поиске фильма.")


@dp.callback_query(lambda callback: callback.data.startswith("search_"))
async def paginate_search(callback: types.CallbackQuery):
    _, query, page = callback.data.split("_")
    page = int(page)

    search_url = f"{API_URL}search/{query}/"
    response = requests.get(search_url)

    if response.status_code == 200:
        movies = response.json().get("results", [])
        if not movies:
            await callback.answer("❌ Фильмы не найдены.")
            return

        await send_paginated_search_results(callback.message, movies, query, page)

    await callback.answer()


async def send_paginated_search_results(message: types.Message, movies, query, page: int):
    start_idx = page * MOVIES_PER_PAGE
    end_idx = start_idx + MOVIES_PER_PAGE
    paginated_movies = movies[start_idx:end_idx]

    text = f"🔍 Найденные фильмы по запросу: {query}\n\n"
    for movie in paginated_movies:
        text += f"📽️ {movie['title']}\n➡️ /download_{movie['id']}\n\n"

    keyboard = InlineKeyboardBuilder()

    if page > 0:
        keyboard.button(text="⬅️ Назад", callback_data=f"search_{query}_{page - 1}")

    if end_idx < len(movies):
        keyboard.button(text="➡️ Вперед", callback_data=f"search_{query}_{page + 1}")

    await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


async def get_top_movies(top_movie_id):
    url = API_URL + 'top-movies/1/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        movies = data.get("movies", [])

        if not movies:
            return "В этом топе пока нет фильмов."

        movies_text = "\n\n".join(
            [
                f"🎬 {movie['title']}\n"
                f"📌 Жанр: {movie['type']}\n"
                f"⭐ Оценки: {movie['stars']}\n"
                f"📅 Год выпуска: {movie['film_year_manufacture']}"
                for movie in movies
            ]
        )

        return f"🔥 Топ фильмов:\n\n{movies_text}"

    return "Ошибка при получении данных."


@dp.message(Command("top"))
async def send_top_movies(message: types.Message):
    top_movie_id = 1  # Можно менять ID топа, если у тебя несколько списков
    top_movies_text = await get_top_movies(top_movie_id)

    await message.answer(top_movies_text, parse_mode="html")




async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
