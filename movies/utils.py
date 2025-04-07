from asgiref.sync import sync_to_async
from movies.models import TelegramUser

@sync_to_async
def get_user_language(user_id):
    user, created = TelegramUser.objects.get_or_create(user_id=user_id)
    return user.language

@sync_to_async
def set_user_language(user_id, lang):
    user, created = TelegramUser.objects.get_or_create(user_id=user_id)
    user.language = lang
    user.save()
