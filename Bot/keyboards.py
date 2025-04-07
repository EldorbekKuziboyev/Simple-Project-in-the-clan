from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import MOVIES_PER_PAGE
from aiogram import types

def create_language_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")
    )
    return keyboard

def create_movie_keyboard(movies):
    keyboard = InlineKeyboardBuilder()
    for idx, movie in enumerate(movies, start=1):
        keyboard.button(text=str(idx), callback_data=f"download_{movie['id']}")
    keyboard.adjust(5)
    return keyboard

def create_pagination_keyboard(target, page, has_next):
    pagination_row = InlineKeyboardBuilder()
    if page > 0:
        pagination_row.button(text="⬅️ ", callback_data=f"movies_{page - 1}")

    if isinstance(target, types.CallbackQuery):
        delete_button = InlineKeyboardButton(text="❌", callback_data=f"delete_{target.message.message_id}")
    else:
        delete_button = InlineKeyboardButton(text="❌", callback_data=f"delete_{target.message_id}")
    pagination_row.add(delete_button)

    if has_next:
        pagination_row.button(text="➡️ ", callback_data=f"movies_{page + 1}")

    return pagination_row