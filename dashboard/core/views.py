from uuid import uuid4

from django.shortcuts import redirect, render

from core.services.forecast import get_five_day_forecast
from core.services.scraping import get_weather_details, get_weather_news
from core.services.weather import get_current_weather


def home(request):
    return render(request, "core/base.html")


def identify(request):
    if request.method != "POST":
        return redirect("home")

    user_name = request.POST.get("user_name", "").strip()
    if not user_name:
        request.session["identify_error"] = "Введите имя пользователя"
        return redirect("home")

    request.session["user_name"] = user_name
    request.session["user_id"] = uuid4().hex
    request.session.pop("identify_error", None)
    request.dashboard_result = f"пользователь {user_name} вошел"
    return redirect("home")


def weather_view(request):
    user_response = _require_user(request)
    if user_response:
        return user_response

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
    user_response = _require_user(request)
    if user_response:
        return user_response

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


def details_view(request):
    user_response = _require_user(request)
    if user_response:
        return user_response

    city = request.GET.get("city", "Москва")
    details = None
    error = None
    try:
        details = get_weather_details(city)
        request.dashboard_result = details["summary"]
    except ValueError as exc:
        error = str(exc)
        request.dashboard_result = f"ошибка: {error}"

    return render(
        request,
        "core/details.html",
        {"details": details, "city": city, "error": error},
    )


def weather_news_view(request):
    user_response = _require_user(request)
    if user_response:
        return user_response

    news = None
    error = None
    try:
        news = get_weather_news()
        request.dashboard_result = news["summary"]
    except ValueError as exc:
        error = str(exc)
        request.dashboard_result = f"ошибка: {error}"

    return render(
        request,
        "core/weather_news.html",
        {"news": news, "error": error},
    )


def _require_user(request):
    if request.session.get("user_id"):
        return None

    request.dashboard_result = "требуется ввод имени пользователя"
    return render(
        request,
        "core/base.html",
        {"identify_error": "Введите имя, чтобы начать работу"},
    )
