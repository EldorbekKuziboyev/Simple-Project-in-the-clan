import os
import sys
import django
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
import aiohttp
import gettext
from config import API_URL, LOCALES_PATH
from movies.utils import get_user_language


async def fetch(url, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            return None

async def get_translation(user_id):
    lang = await get_user_language(user_id)
    return gettext.translation('messages', localedir=LOCALES_PATH, languages=[lang])

async def get_channels():
    channels = await fetch(f"{API_URL}channels/")
    return channels if channels else {}