import re
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup


WTTR_URL = "https://wttr.in/{city}"
GISMETEO_NEWS_URL = "https://www.gismeteo.ru/news/"


def get_weather_details(city):
    response = requests.get(
        WTTR_URL.format(city=quote(city)),
        params={"format": "%t|%w|%P", "lang": "ru"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    if response.status_code != 200:
        raise ValueError(
            f"Не удалось получить погодные детали для города {city}: "
            f"HTTP {response.status_code}"
        )

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    temperature, wind, pressure = _parse_wttr_details(text)

    return {
        "city": city,
        "temperature": temperature or "нет данных",
        "wind": wind or "нет данных",
        "pressure": pressure or "нет данных",
        "summary": f"детали погоды для {city} получены",
    }


def get_weather_news(limit=5):
    response = requests.get(
        GISMETEO_NEWS_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    if response.status_code != 200:
        raise ValueError(
            f"Не удалось получить новости погоды: HTTP {response.status_code}"
        )

    soup = BeautifulSoup(response.text, "html.parser")
    items = []
    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        href = link.get("href")
        if not title or len(title) < 12:
            continue

        normalized = title.lower()
        if not any(word in normalized for word in _weather_words()):
            continue

        item = {"title": title, "url": urljoin(GISMETEO_NEWS_URL, href)}
        if item not in items:
            items.append(item)
        if len(items) == limit:
            break

    return {
        "items": items,
        "summary": f"{len(items)} новостей погоды загружено",
    }


def _first_match(pattern, text):
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _parse_wttr_details(text):
    compact_text = " ".join(text.split())
    formatted = re.search(
        r"([+-]?\d+\s*°C)\|([^|]+)\|([^\s<]+)",
        compact_text,
        flags=re.IGNORECASE,
    )
    if formatted:
        return (
            formatted.group(1).strip(),
            formatted.group(2).strip(),
            formatted.group(3).strip(),
        )

    temperature = _first_match(r"([+-]?\d+\s*°C)", text)
    wind = _first_match(r"Ветер:?\s*([^,;]+)", text)
    pressure = _first_match(r"Давление:?\s*([^,;]+)", text)
    return temperature, wind, pressure


def _weather_words():
    return ("погод", "дожд", "снег", "ветер", "жар", "мороз", "циклон")
