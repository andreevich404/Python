import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def bot_token():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Set BOT_TOKEN in .env")
    return token


def yandex_geocoder_key():
    key = os.getenv("YANDEX_GEOCODER_API_KEY")
    if not key:
        raise RuntimeError("Set YANDEX_GEOCODER_API_KEY in .env")
    return key
