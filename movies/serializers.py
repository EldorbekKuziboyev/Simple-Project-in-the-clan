from rest_framework import serializers
from .models import Movie, MovieType, TopMovie, Channel


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('id', 'title', 'type', 'video_file', 'stars', 'film_year_manufacture','file_id')

class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ["chat_id", "link"]


class MovieTopSerializer(serializers.ModelSerializer):
    movies = MovieSerializer(many=True)

    class Meta:
        model = TopMovie
        fields = ("id", "movies")