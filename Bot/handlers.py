import gettext
from aiogram import types
import os
import sys
import django
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import MOVIES_PER_PAGE, API_URL, CHANNEL_ID, LOCALES_PATH, bot
from movies.utils import set_user_language, get_user_language
from services import fetch, get_translation, get_channels
from keyboards import create_language_keyboard, create_movie_keyboard, create_pagination_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()


async def start(message: types.Message):
    keyboard = create_language_keyboard()
    await message.answer("Select language/Tilni tanlang/Выберите язык:", reply_markup=keyboard.as_markup())

async def set_language(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = call.data.split("_")[1]
    await set_user_language(user_id, lang)
    translation = gettext.translation('messages', localedir=LOCALES_PATH, languages=[lang])
    translation.install()
    await call.message.edit_text(_("start"))
    await call.answer()


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
                # Получаем язык пользователя
                lang = await get_user_language(user_id)

                # Используем метод get_title для получения title на нужном языке
                title = movie_data.get(f"title_{lang}", movie_data.get("title_ru", _("unknown_title")))
                movie_type = movie_data.get("type", [_("unknown_type")])
                stars = movie_data.get("stars", _("unknown_stars"))
                year = movie_data.get("film_year_manufacture", _("unknown_year"))

                await bot.copy_message(
                    chat_id=call.message.chat.id,
                    from_chat_id=CHANNEL_ID,
                    message_id=message_id,
                    caption=f"🎬 {title}\n"
                            f"📌 {_('type')}: {', '.join(movie_type)}\n"
                            f"⭐️ {_('stars')}: {stars}\n"
                            f"📅 {_('year')}: {year[:4] if year else _('unknown_year')}"
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

async def paginate_search(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    translation = await get_translation(user_id)
    translation.install()

    _, query, page = callback.data.split("_")
    page = int(page)

    search_url = f"{API_URL}search/{query}/"
    movies = await fetch(search_url)

    if movies:
        await send_paginated_search_results(callback.message, movies.get("results", []), query, page)
    else:
        await callback.answer(_("no_movies"))

async def send_paginated_search_results(message: types.Message, movies, query, page: int):
    user_id = message.from_user.id
    translation = await get_translation(user_id)
    translation.install()

    start_idx = page * MOVIES_PER_PAGE
    end_idx = start_idx + MOVIES_PER_PAGE
    paginated_movies = movies[start_idx:end_idx]

    text = _("search_results").format(query=query) + "\n"
    for idx, movie in enumerate(paginated_movies, start=1):
        text += f"{idx}. 📽️ {movie['title']}\n"

    keyboard = InlineKeyboardBuilder()

    for idx, movie in enumerate(paginated_movies, start=1):
        keyboard.button(text=str(idx), callback_data=f"download_{movie['id']}")

    keyboard.adjust(5)

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

async def error_handler(event: types.ErrorEvent):
    logger.error(f"Ошибка: {event.exception}")
    await event.update.message.answer(_("error"))