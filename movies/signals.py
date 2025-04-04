from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Movie
from .tasks import send_movie_to_channel

@receiver(post_save, sender=Movie)
def movie_created(sender, instance, created, **kwargs):
    if created:
        print(f"signal worked: {instance.id}.")
        send_movie_to_channel.delay(instance.id)
