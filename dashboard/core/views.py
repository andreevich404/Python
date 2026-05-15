from django.shortcuts import render

from core.services.currency import get_currency_rate
from core.services.forecast import get_five_day_forecast
from core.services.news import get_news
from core.services.weather import get_current_weather


def home(request):
    return render(request, "core/base.html")


def weather_view(request):
    city = request.GET.get("city", "Москва")
    weather = None
    error = None
    try:
        weather = get_current_weather(city)
        request.dashboard_result = weather["summary"]
    except ValueError as exc:
        error = str(exc)
        request.dashboard_result = f"ошибка: {error}"

    return render(
        request,
        "core/weather.html",
        {"weather": weather, "city": city, "error": error},
    )


def forecast_view(request):
    city = request.GET.get("city", "Москва")
    forecast = None
    error = None
    try:
        forecast = get_five_day_forecast(city)
        request.dashboard_result = forecast["summary"]
    except ValueError as exc:
        error = str(exc)
        request.dashboard_result = f"ошибка: {error}"

    return render(
        request,
        "core/forecast.html",
        {"forecast": forecast, "city": city, "error": error},
    )


def currency_view(request):
    code = request.GET.get("code", "USD")
    currency = get_currency_rate(code)
    request.dashboard_result = currency["summary"]
    return render(
        request,
        "core/currency.html",
        {"currency": currency, "code": code.upper()},
    )


def news_view(request):
    news = get_news()
    request.dashboard_result = news["summary"]
    return render(request, "core/news.html", {"news": news})
