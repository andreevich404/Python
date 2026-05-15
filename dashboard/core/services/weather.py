import os

import requests


OPENWEATHERMAP_WEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)


def get_current_weather(city):
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        raise ValueError("OPENWEATHERMAP_API_KEY не задан")

    response = requests.get(
        OPENWEATHERMAP_WEATHER_URL,
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
            f"Не удалось получить погоду для города {city}: "
            f"HTTP {response.status_code}"
        )

    payload = response.json()
    temperature = round(payload["main"]["temp"])
    description = payload["weather"][0]["description"]

    return {
        "city": payload.get("name", city),
        "temperature": temperature,
        "feels_like": round(payload["main"].get("feels_like", temperature)),
        "humidity": payload["main"].get("humidity"),
        "wind_speed": payload.get("wind", {}).get("speed"),
        "description": description,
        "summary": f"{temperature}°C, {description}",
    }
