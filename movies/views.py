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
        movies = Movie.objects.all()
        serializer = MovieSerializer(movies, many=True)
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
            Movie.objects.only("id", "file_id", "type", "title", "film_year_manufacture", "stars"), id=movie_id)

        if movie.file_id:
            types = [t.title for t in
                     movie.type.all()]  # Преобразуем объекты ManyToMany в список их названий или других атрибутов
            return Response({
                "file_id": movie.file_id,
                "type": types,  # Печатаем список названий или любых других атрибутов объектов типа
                "title": movie.title,
                "film_year_manufacture": movie.film_year_manufacture,
                "stars": movie.stars
            })
        return Response({"error": "Файл еще не загружен в Telegram"}, status=400)


class MovieSearchAPIView(APIView):
    class MoviePagination(PageNumberPagination):
        page_size = 10  # Количество элементов на странице
        page_size_query_param = 'page_size'
        max_page_size = 100

    def get(self, request, title):
        movies = Movie.objects.filter(Q(title__icontains=title))
        paginator = self.MoviePagination()
        result_page = paginator.paginate_queryset(movies, request)
        serializer = MovieSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TopMoviesAPIView(APIView):
    def get(self, request, top_movie_id):
        top_movie = get_object_or_404(TopMovie, id=top_movie_id)
        serializer = MovieTopSerializer(top_movie)
        return Response(serializer.data)