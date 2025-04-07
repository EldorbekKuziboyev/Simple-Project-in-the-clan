import os
from aiogram import Bot, Dispatcher

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOKEN = "7593798870:AAGCPzzkKBdBjHS_dY0851eoXjbuQ4AJ3Rs"
API_URL = "https://8685-86-62-2-250.ngrok-free.app/api/movies/"
CHANNEL_ID = -1002359210651
MOVIES_PER_PAGE = 10
LOCALES_PATH = os.path.join(os.path.dirname(__file__), 'locales')

bot = Bot(token=TOKEN)
dp = Dispatcher()