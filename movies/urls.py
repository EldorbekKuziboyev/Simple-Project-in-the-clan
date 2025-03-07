from django.urls import path
from .views import MovieListAPIView, UploadMovieAPIView, MovieDownloadAPIView, MovieSearchAPIView, TopMoviesAPIView, \
    ChannelListAPIView

urlpatterns = [
    path('movies/', MovieListAPIView.as_view(), name='movie-list'),
    path('upload/', UploadMovieAPIView.as_view(), name='upload-movie'),
    path('movies/<int:movie_id>/download/', MovieDownloadAPIView.as_view(), name='download-movie'),
    path('movies/search/<str:title>/', MovieSearchAPIView.as_view(), name='search-movie'),
    path("movies/top-movies/<int:top_movie_id>/", TopMoviesAPIView.as_view(), name="top-movies"),
    path("movies/channels/", ChannelListAPIView.as_view(), name="channel-list"),
]
