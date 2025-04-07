from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class TelegramUser(models.Model):
    user_id = models.BigIntegerField(unique=True)
    language = models.CharField(max_length=5, default="ru")

    def __str__(self):
        return f'{self.user_id} = {self.language}'

class Channel(models.Model):
    chat_id = models.CharField(max_length=50, unique=True)
    link = models.URLField()

    def __str__(self):
        return self.chat_id

class MovieType(models.Model):
    title = models.CharField(_('title'), max_length=255)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("MovieType")
        verbose_name_plural = _("MovieType")

from django.db import models
from django.utils.translation import gettext_lazy as _

# movies/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Movie(models.Model):
    STARS_CHOICES = [
        ('️️️⭐️', '1'),
        ('⭐️⭐️', '2'),
        ('⭐️⭐️⭐️', '️3'),
        ('⭐️⭐️⭐️⭐️', '4'),
        ('⭐️⭐️⭐️⭐️⭐️', '5'),
    ]
    title = models.CharField(null=True,blank=True)
    title_ru = models.CharField(_("Название (рус)"), max_length=255, db_index=True, blank=True, null=True)
    title_en = models.CharField(_("Название (англ)"), max_length=255, db_index=True, blank=True, null=True)
    title_uz = models.CharField(_("Название (узб)"), max_length=255, db_index=True, blank=True, null=True)

    video_file = models.FileField(_('video_file'))
    type = models.ManyToManyField('MovieType')
    thumbnail = models.FileField(blank=True, null=True)
    film_year_manufacture = models.DateField(_('Film created year'), blank=True, null=True, db_index=True)
    stars = models.CharField(_('stars'), max_length=10, choices=STARS_CHOICES, blank=True, null=True)
    file_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    # def __str__(self):
    #     return self.title_ru

    def get_title(self, lang='ru'):
        if lang == 'ru':
            return self.title_ru
        elif lang == 'en':
            return self.title_en or self.title_ru  # Fallback на русский, если английский отсутствует
        elif lang == 'uz':
            return self.title_uz or self.title_ru  # Fallback на русский, если узбекский отсутствует
        return self.title_ru

    class Meta:
        verbose_name = _("Movie")
        verbose_name_plural = _("Movie")

    def __str__(self):
        return self.title



class TopMovie(models.Model):
    movies = models.ManyToManyField(Movie)

    class Meta:
        verbose_name = _("Top Movie")
        verbose_name_plural = _("Top Movie")