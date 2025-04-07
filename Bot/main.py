import os
import sys
import django
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from config import BASE_DIR, TOKEN
from handlers import start, set_language, delete_message, download_movie, check_subscription, search_movies, paginate_search, send_paginated_search_results, error_handler

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.message.register(start, Command("start", "language"))
dp.callback_query.register(set_language, lambda call: call.data.startswith("lang_"))
dp.callback_query.register(delete_message, lambda callback: callback.data.startswith("delete_"))
dp.callback_query.register(download_movie, lambda call: call.data.startswith("download_"))
dp.callback_query.register(check_subscription, lambda call: call.data == "check_sub")
dp.message.register(search_movies, lambda message: not message.text.startswith("/"))
dp.callback_query.register(paginate_search, lambda callback: callback.data.startswith("search_"))
dp.errors.register(error_handler)

async def main():
    print("🤖 -... --- - / .-- --- .-. -.- . -..")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())