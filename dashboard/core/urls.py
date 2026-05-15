from django.urls import path

from core import views


urlpatterns = [
    path("", views.home, name="home"),
    path("weather/", views.weather_view, name="weather"),
    path("forecast/", views.forecast_view, name="forecast"),
    path("currency/", views.currency_view, name="currency"),
    path("news/", views.news_view, name="news"),
]
