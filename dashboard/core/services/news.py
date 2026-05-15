from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


LENTA_URL = "https://lenta.ru"


def get_news(limit=5):
    response = requests.get(LENTA_URL, timeout=10)
    if response.status_code != 200:
        raise ValueError("Не удалось получить новости")

    soup = BeautifulSoup(response.text, "html.parser")
    items = []
    for link in soup.select("a.card-mini, a[href^='/news/']"):
        title = link.get_text(" ", strip=True)
        href = link.get("href")
        if not title or not href:
            continue

        item = {"title": title, "url": urljoin(LENTA_URL, href)}
        if item not in items:
            items.append(item)
        if len(items) == limit:
            break

    return {"items": items, "summary": f"{len(items)} новостей загружено"}
