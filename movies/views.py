from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Movie, TopMovie
from .serializers import MovieSerializer, MovieTopSerializer
from .tasks import send_movie_to_channel
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Channel
from .serializers import ChannelSerializer

class ChannelListAPIView(APIView):
    def get(self, request):
        channels = Channel.objects.all()
        serializer = ChannelSerializer(channels, many=True)
        return Response({ch["chat_id"]: ch["link"] for ch in serializer.data})


class MovieListAPIView(APIView):
    def get(self, request):
        lang = request.META.get('HTTP_ACCEPT_LANGUAGE', 'ru')  # Получаем язык из заголовка
        movies = Movie.objects.all()
        serializer = MovieSerializer(movies, many=True, context={'lang': lang})
        return Response(serializer.data)

class UploadMovieAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = MovieSerializer(data=request.data)
        if serializer.is_valid():
            movie = serializer.save()
            send_movie_to_channel.delay(movie.id)
            cache.delete("movies")  # Удаляем кеш, чтобы обновить список
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MovieDownloadAPIView(APIView):
    def get(self, request, movie_id):
        movie = get_object_or_404(
            Movie.objects.prefetch_related('type').only("id", "file_id", "type", "title_ru", "title_uz", "title_en", "film_year_manufacture", "stars"),
            id=movie_id
        )
        if movie.file_id:
            types = [t.title for t in movie.type.all()]
            return Response({
                "file_id": movie.file_id,
                "type": types,
                "title_ru": movie.title_ru,
                "title_en": movie.title_en,
                "title_uz": movie.title_uz,
                "film_year_manufacture": movie.film_year_manufacture,
                "stars": movie.stars
            })
        return Response({"error": "Файл еще не загружен в Telegram"}, status=400)


class MovieSearchAPIView(APIView):
    class MoviePagination(PageNumberPagination):
        page_size = 100
        page_size_query_param = 'page_size'
        max_page_size = 100

    def get(self, request, title):
        print(f"Received title: {title}")  # Проверьте, что title правильно декодирован
        movies = Movie.objects.filter(title__icontains=title)
        paginator = self.MoviePagination()
        result_page = paginator.paginate_queryset(movies, request)
        serializer = MovieSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)



class TopMoviesAPIView(APIView):
    def get(self, request, top_movie_id):
        top_movie = get_object_or_404(
            TopMovie.objects.prefetch_related('movies__type'),
            id=top_movie_id
        )
        serializer = MovieTopSerializer(top_movie)
        data = serializer.data

        for movie in data["movies"]:
            movie_obj = Movie.objects.get(id=movie["id"])
            movie["type"] = [t.title for t in movie_obj.type.all()]

        return Response(data)