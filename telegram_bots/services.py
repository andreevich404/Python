import json
import re
import ssl
from dataclasses import dataclass
from html import unescape
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

import certifi

from telegram_bots.config import yandex_geocoder_key


SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def fetch_json_url(url, params=None):
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "Lab9Bot/1.0"})
    with urlopen(request, timeout=20, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_html(url):
    request = Request(url, headers={"User-Agent": "Lab9Bot/1.0"})
    with urlopen(request, timeout=20, context=SSL_CONTEXT) as response:
        return response.read().decode("utf-8")


def yandex_static_map_url(lon, lat):
    params = {
        "ll": f"{lon},{lat}",
        "z": 15,
        "l": "map",
        "pt": f"{lon},{lat},pm2rdm",
        "size": "650,450",
    }
    return "https://static-maps.yandex.ru/1.x/?" + urlencode(params)


def yandex_geocode(query):
    params = {
        "apikey": yandex_geocoder_key(),
        "geocode": query,
        "format": "json",
        "lang": "ru_RU",
    }
    payload = fetch_json_url("https://geocode-maps.yandex.ru/v1/", params)
    collection = payload["response"]["GeoObjectCollection"]
    members = collection["featureMember"]
    if not members:
        return None
    geoobject = members[0]["GeoObject"]
    lon, lat = geoobject["Point"]["pos"].split()
    return geoobject["name"], geoobject["description"], float(lon), float(lat)


async def translate_text(text, source, target):
    import asyncio

    data = await asyncio.to_thread(
        fetch_json_url,
        "https://api.mymemory.translated.net/get",
        {"q": text, "langpair": f"{source}|{target}"},
    )
    return data["responseData"]["translatedText"]


@dataclass
class Product:
    name: str
    price: float
    url: str
    image: str
    description: str


def parse_products_from_listing(html, base_url):
    pattern = (
        r'<div class="col-lg-4 col-md-6 mb-4">'
        r'(.+?)</div>\s*</div>'
    )
    cards = re.findall(pattern, html, re.S)
    products = []
    for card in cards:
        href = re.search(r'href="([^"]+)"', card)
        image = re.search(
            r'<img class="card-img-top img-fluid" src="([^"]+)"',
            card,
        )
        name = re.search(
            r'<h4 class="card-title"><a[^>]*>(.*?)</a></h4>',
            card,
            re.S,
        )
        price = re.search(r"<h5>\s*\$(.*?)\s*</h5>", card)
        if href and image and name and price:
            products.append(
                Product(
                    name=unescape(
                        re.sub(r"\s+", " ", name.group(1)).strip()
                    ),
                    price=float(price.group(1)),
                    url=urljoin(base_url, href.group(1)),
                    image=urljoin(base_url, image.group(1)),
                    description="",
                )
            )
    return products


def parse_description(html):
    match = re.search(r'<p class="card-text">(.*?)</p>', html, re.S)
    if not match:
        return ""
    return unescape(re.sub(r"\s+", " ", match.group(1)).strip())


def collect_scrapingclub_products():
    base_url = "https://scrapingclub.com"
    page_url = base_url + "/exercise/list_basic/?page=1"
    products = []
    while page_url:
        html = fetch_html(page_url)
        products.extend(parse_products_from_listing(html, base_url))
        next_page = re.search(
            r'<li class="page-item">\s*'
            r'<a class="page-link" href="([^"]+)">Next</a>',
            html,
        )
        page_url = urljoin(base_url, next_page.group(1)) if next_page else None
    for product in products:
        product.description = parse_description(fetch_html(product.url))
    return products


def closest_product(target_price):
    products = collect_scrapingclub_products()
    if not products:
        raise RuntimeError("Products not found")
    return min(
        products,
        key=lambda product: (
            abs(product.price - target_price),
            product.name.lower(),
        ),
    )
