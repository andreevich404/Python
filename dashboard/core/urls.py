from django.urls import path

from core import views


urlpatterns = [
    path("", views.home, name="home"),
    path("identify/", views.identify, name="identify"),
    path("weather/", views.weather_view, name="weather"),
    path("forecast/", views.forecast_view, name="forecast"),
    path("details/", views.details_view, name="details"),
    path("weather-news/", views.weather_news_view, name="weather_news"),
]
