from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

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

class Movie(models.Model):
    STARS_CHOICES = [
        ('️️️⭐️', '1'),
        ('⭐️⭐️', '2'),
        ('⭐️⭐️⭐️', '️3'),
        ('⭐️⭐️⭐️⭐️', '4'),
        ('⭐️⭐️⭐️⭐️⭐️', '5'),
    ]

    title = models.CharField(_('title'), max_length=255)
    video_file = models.FileField(_('video_file'))
    type = models.ManyToManyField(MovieType)
    thumbnail = models.FileField(blank=True, null=True)
    film_year_manufacture = models.DateField(_('Film created year'), blank=True, null=True)
    stars = models.CharField(_('stars'), max_length=10, choices=STARS_CHOICES, blank=True, null=True)
    file_id = models.CharField( max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)  # Дата создания фильма

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.film_year_manufacture:
            self.film_year_manufacture = self.film_year_manufacture.replace(month=1, day=1)  # Привести к 1 января
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Movie")
        verbose_name_plural = _("Movie")

class TopMovie(models.Model):
    movies = models.ManyToManyField(Movie)

    class Meta:
        verbose_name = _("Top Movie")
        verbose_name_plural = _("Top Movie")