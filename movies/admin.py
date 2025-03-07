import json
from django.db.models import Q

from django.contrib.admin.models import LogEntry
from django.db.models import Count
from .models import Movie, MovieType, TopMovie, Channel
from datetime import timedelta
from django.utils.timezone import now
from django.contrib import admin
from django.urls import path
from django.shortcuts import render

class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "display_movie_types")

    def display_movie_types(self, obj):
        return ", ".join([t.title for t in obj.type.all()])
    display_movie_types.short_description = "Типы"

    def changelist_view(self, request, extra_context=None):
        # Группируем фильмы по их типам и считаем количество
        movie_counts = (
            MovieType.objects
            .annotate(count=Count("movie"))
            .order_by("-count")
        )

        labels = [mt.title for mt in movie_counts]
        data = [mt.count for mt in movie_counts]

        chart_data = {
            "labels": labels,
            "datasets": [
                {
                    "label": "Количество фильмов по типам",
                    "data": data,
                    "backgroundColor": [
                        "rgba(255, 99, 132, 0.5)",
                        "rgba(54, 162, 235, 0.5)",
                        "rgba(255, 206, 86, 0.5)",
                        "rgba(75, 192, 192, 0.5)",
                        "rgba(153, 102, 255, 0.5)",
                        "rgba(255, 159, 64, 0.5)"
                    ],
                    "borderColor": [
                        "rgba(255, 99, 132, 1)",
                        "rgba(54, 162, 235, 1)",
                        "rgba(255, 206, 86, 1)",
                        "rgba(75, 192, 192, 1)",
                        "rgba(153, 102, 255, 1)",
                        "rgba(255, 159, 64, 1)"
                    ],
                    "borderWidth": 1
                }
            ]
        }

        extra_context = extra_context or {}
        extra_context["chart_data"] = json.dumps(chart_data)
        return super().changelist_view(request, extra_context)

admin.site.register(Movie, MovieAdmin)
admin.site.register(MovieType)
admin.site.register(TopMovie)
admin.site.register(Channel)

