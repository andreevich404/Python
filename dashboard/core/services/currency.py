import xml.etree.ElementTree as ET

import requests


CBR_DAILY_URL = "https://www.cbr.ru/scripts/XML_daily.asp"


def get_currency_rate(code):
    normalized_code = code.upper()
    response = requests.get(CBR_DAILY_URL, timeout=10)
    if response.status_code != 200:
        raise ValueError("Не удалось получить курсы валют ЦБ РФ")

    root = ET.fromstring(response.content)
    for valute in root.findall("Valute"):
        char_code = valute.findtext("CharCode")
        if char_code == normalized_code:
            nominal = int(valute.findtext("Nominal", "1"))
            rate = float(valute.findtext("Value", "0").replace(",", "."))
            return {
                "code": normalized_code,
                "nominal": nominal,
                "name": valute.findtext("Name", normalized_code),
                "rate": rate,
                "summary": f"{nominal} {normalized_code} = {rate:.2f} RUB",
            }

    raise ValueError(f"Валюта {normalized_code} не найдена")
