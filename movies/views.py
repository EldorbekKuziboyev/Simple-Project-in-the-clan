from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import Movie
from .serializers import MovieSerializer
from .tasks import send_movie_to_channel

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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MovieDownloadAPIView(APIView):
    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        if movie.file_id:
            return Response({"file_id": movie.file_id})
        return Response({"error": "Файл еще не загружен в Telegram"}, status=400)
