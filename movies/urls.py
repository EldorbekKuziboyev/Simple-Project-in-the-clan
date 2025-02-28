from django.urls import path
from .views import MovieListAPIView, UploadMovieAPIView, MovieDownloadAPIView

urlpatterns = [
    path('movies/', MovieListAPIView.as_view(), name='movie-list'),
    path('upload/', UploadMovieAPIView.as_view(), name='upload-movie'),
    path('movies/<int:movie_id>/download/', MovieDownloadAPIView.as_view(), name='download-movie'),
]
