import os
import sys
import django
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
import asyncio
import aiohttp
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import gettext
from movies.utils import get_user_language, set_user_language


TOKEN = "7593798870:AAGCPzzkKBdBjHS_dY0851eoXjbuQ4AJ3Rs"
API_URL = "https://2f12-86-62-2-249.ngrok-free.app/api/movies/"
CHANNEL_ID = -1002359210651

bot = Bot(token=TOKEN)
dp = Dispatcher()

locales_path = os.path.join(os.path.dirname(__file__), 'locales')
ru = gettext.translation('messages', localedir=locales_path, languages=['ru'])
ru.install()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOVIES_PER_PAGE = 10

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None

@dp.message(Command("start", "language"))
async def start(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")
    )
    await message.answer("Select language/Tilni tanlang/Выберите язык:", reply_markup=keyboard.as_markup())

@dp.callback_query(lambda call: call.data.startswith("lang_"))
async def set_language(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = call.data.split("_")[1]

    await set_user_language(user_id, lang)

    translation = gettext.translation('messages', localedir=locales_path, languages=[lang])
    translation.install()

    await call.message.edit_text(_("start"))
    await call.answer()

# Получение перевода для пользователя
async def get_translation(user_id):
    lang = await get_user_language(user_id)
    return gettext.translation('messages', localedir=locales_path, languages=[lang])

@dp.message(Command("movies"))
async def get_movies(message: types.Message, page: int = 0):
    await paginate(message, page)

async def paginate(target: types.Message | types.CallbackQuery, page: int):
    user_id = target.from_user.id
    translation = await get_translation(user_id)
    translation.install()

    movies = await fetch(API_URL)
    if not movies:
        text = _("no_movies")
        if isinstance(target, types.Message):
            await target.answer(text)
        else:
            await target.answer(text, show_alert=True)
        return

    total_pages = (len(movies) + MOVIES_PER_PAGE - 1) // MOVIES_PER_PAGE
    if page < 0 or page >= total_pages:
        await target.answer(_("invalid_page"))
        return

    start_idx = page * MOVIES_PER_PAGE
    end_idx = start_idx + MOVIES_PER_PAGE
    paginated_movies = movies[start_idx:end_idx]

    text = _("movies_list")
    for idx, movie in enumerate(paginated_movies, start=1):
        text += f"{idx}.📽️ {movie['title']}\n"

    keyboard = InlineKeyboardBuilder()
    for idx, movie in enumerate(paginated_movies, start=1):
        keyboard.button(text=str(idx), callback_data=f"download_{movie['id']}")
    keyboard.adjust(5)

    if page > 0 or end_idx < len(movies):
        pagination_row = InlineKeyboardBuilder()
        if page > 0:
            pagination_row.button(text="⬅️ " + _("back"), callback_data=f"movies_{page - 1}")

        if isinstance(target, types.CallbackQuery):
            delete_button = InlineKeyboardButton(text="❌", callback_data=f"delete_{target.message.message_id}")
        else:
            delete_button = InlineKeyboardButton(text="❌", callback_data=f"delete_{target.message_id}")
        pagination_row.add(delete_button)

        if end_idx < len(movies):
            pagination_row.button(text="➡️ " + _("forward"), callback_data=f"movies_{page + 1}")

        keyboard.attach(pagination_row)

    if isinstance(target, types.Message):
        await target.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
    else:
        await target.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        await target.answer()

@dp.callback_query(lambda callback: callback.data.startswith("delete_"))
async def delete_message(callback: types.CallbackQuery):
    # Получаем message_id из callback_data
    message_id = int(callback.data.split("_")[1])

    try:
        # Удаляем сообщение
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")
        await callback.answer("Не удалось удалить сообщение.", show_alert=True)
    else:
        await callback.answer("Сообщение удалено.", show_alert=True)

@dp.callback_query(lambda callback: callback.data.startswith("movies_"))
async def paginate_movies(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[1])
    await paginate(callback, page)

# Получение списка каналов
async def get_channels():
    channels = await fetch(f"{API_URL}channels/")
    return channels if channels else {}

# Обработка загрузки фильма
@dp.callback_query(lambda call: call.data.startswith("download_"))
async def download_movie(call: types.CallbackQuery):
    user_id = call.from_user.id
    translation = await get_translation(user_id)
    translation.install()

    movie_id = call.data.split("_")[1]
    movie_url = f"{API_URL}{movie_id}/download/"

    channels = await get_channels()
    not_subscribed = []

    for chat_id, link in channels.items():
        user_status = await bot.get_chat_member(chat_id=int(chat_id), user_id=user_id)
        if user_status.status not in ["member", "administrator", "creator"]:
            not_subscribed.append((chat_id, link))

    if not not_subscribed:
        movie_data = await fetch(movie_url)
        if movie_data:
            message_id = movie_data.get("file_id")

            if not message_id:
                await call.message.answer(_("error"))
                return

            try:
                await bot.copy_message(
                    chat_id=call.message.chat.id,
                    from_chat_id=CHANNEL_ID,
                    message_id=message_id,
                    caption=f"🎬 {movie_data['title']}\n"
                            f"📌 Жанр: {', '.join(movie_data['type'])}\n"
                            f"⭐️ Оценки: {movie_data['stars']}\n"
                            f"📅 Год выпуска: {movie_data['film_year_manufacture'][:4]}"
                )
            except Exception as e:
                await call.message.answer(f"❌ {_('copy_error')}: {e}")
        else:
            await call.message.answer(_("error"))
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"🔗 {_('subscribe_channel')} {i+1}", url=link)]
                for i, (chat_id, link) in enumerate(not_subscribed)
            ] + [[InlineKeyboardButton(text="✅ " + _("check_subscription"), callback_data="check_sub")]]
        )

        await call.message.answer(_("not_subscribed"), reply_markup=keyboard)

# Обработка проверки подписки
@dp.callback_query(lambda call: call.data == "check_sub")
async def check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id
    translation = await get_translation(user_id)
    translation.install()

    channels = await get_channels()
    not_subscribed = []

    for chat_id, link in channels.items():
        user_status = await bot.get_chat_member(chat_id=int(chat_id), user_id=user_id)
        if user_status.status not in ["member", "administrator", "creator"]:
            not_subscribed.append((chat_id, link))

    if not not_subscribed:
        await call.message.edit_text(_("subscribed"))
    else:
        await call.answer(_("not_subscribed"), show_alert=True)

# Поиск фильмов
@dp.message(lambda message: not message.text.startswith("/"))
async def search_movies(message: types.Message):
    user_id = message.from_user.id
    translation = await get_translation(user_id)
    translation.install()

    query = message.text.strip()
    if not query:
        return

    search_url = f"{API_URL}search/{query}/"
    movies = await fetch(search_url)

    if movies:
        await send_paginated_search_results(message, movies.get("results", []), query, 0)
    else:
        await message.answer(_("error"))

@dp.callback_query(lambda callback: callback.data.startswith("search_"))
async def paginate_search(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    translation = await get_translation(user_id)
    translation.install()

    # Разбираем callback_data
    _, query, page = callback.data.split("_")
    page = int(page)

    # Получаем фильмы из API
    search_url = f"{API_URL}search/{query}/"
    movies = await fetch(search_url)

    if movies:
        # Редактируем существующее сообщение
        await send_paginated_search_results(callback.message, movies.get("results", []), query, page)
    else:
        await callback.answer(_("no_movies"))

async def send_paginated_search_results(message: types.Message, movies, query, page: int):
    user_id = message.from_user.id
    translation = await get_translation(user_id)
    translation.install()

    # Рассчитываем индексы для пагинации
    start_idx = page * MOVIES_PER_PAGE
    end_idx = start_idx + MOVIES_PER_PAGE
    paginated_movies = movies[start_idx:end_idx]

    # Создаем текст сообщения
    text = _("search_results").format(query=query) + "\n"
    for idx, movie in enumerate(paginated_movies, start=1):
        text += f"{idx}. 📽️ {movie['title']}\n"

    # Создаем клавиатуру
    keyboard = InlineKeyboardBuilder()

    # Добавляем кнопки для фильмов
    for idx, movie in enumerate(paginated_movies, start=1):
        keyboard.button(text=str(idx), callback_data=f"download_{movie['id']}")

    # Группируем кнопки фильмов по 3 в строку
    keyboard.adjust(5)

    # Добавляем кнопки пагинации на отдельной строке
    if page > 0 or end_idx < len(movies):
        pagination_row = InlineKeyboardBuilder()
        if page > 0:
            pagination_row.button(text="⬅️ " + _("back"), callback_data=f"search_{query}_{page - 1}")
        if isinstance(message, types.CallbackQuery):
            delete_button = InlineKeyboardButton(text="❌", callback_data=f"delete_{message.message.message_id}")
        else:
            delete_button = InlineKeyboardButton(text="❌", callback_data=f"delete_{message.message_id}")
        pagination_row.add(delete_button)
        if end_idx < len(movies):
            pagination_row.button(text="➡️ " + _("forward"), callback_data=f"search_{query}_{page + 1}")

        pagination_row.adjust(2)

        keyboard.attach(pagination_row)

    if message.reply_markup:
        try:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


@dp.errors()
async def error_handler(event: types.ErrorEvent):
    logger.error(f"Ошибка: {event.exception}")
    await event.update.message.answer(_("error"))

async def main():
    print("🤖 -... --- - / .-- --- .-. -.- . -..")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())