import os
from collections import defaultdict

import requests


OPENWEATHERMAP_FORECAST_URL = (
    "https://api.openweathermap.org/data/2.5/forecast"
)


def get_five_day_forecast(city):
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        raise ValueError("OPENWEATHERMAP_API_KEY не задан")

    response = requests.get(
        OPENWEATHERMAP_FORECAST_URL,
        params={
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "ru",
        },
        timeout=10,
    )
    if response.status_code != 200:
        raise ValueError(
            f"Не удалось получить прогноз для города {city}: "
            f"HTTP {response.status_code}"
        )

    payload = response.json()
    grouped = defaultdict(list)
    for item in payload["list"]:
        date = item["dt_txt"].split(" ", 1)[0]
        grouped[date].append(item)

    days = []
    for date, points in list(grouped.items())[:5]:
        temperatures = [point["main"]["temp"] for point in points]
        descriptions = [point["weather"][0]["description"] for point in points]
        days.append(
            {
                "date": date,
                "min_temp": round(min(temperatures)),
                "max_temp": round(max(temperatures)),
                "description": max(set(descriptions), key=descriptions.count),
            }
        )

    return {
        "city": payload.get("city", {}).get("name", city),
        "days": days,
        "summary": "прогноз на 5 дней получен",
    }
