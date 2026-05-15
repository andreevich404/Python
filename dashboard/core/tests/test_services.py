from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from core.services.currency import get_currency_rate
from core.services.forecast import get_five_day_forecast
from core.services.news import get_news
from core.services.weather import get_current_weather


class ServiceTests(SimpleTestCase):
    @patch("core.services.weather.requests.get")
    @patch.dict(
        "core.services.weather.os.environ",
        {"OPENWEATHERMAP_API_KEY": "test-key"},
    )
    def test_weather_service_parses_openweathermap_response(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "name": "Москва",
                "main": {"temp": 18.4, "feels_like": 17.8, "humidity": 61},
                "weather": [{"description": "облачно"}],
                "wind": {"speed": 3.5},
            },
        )

        result = get_current_weather("Москва")

        self.assertEqual(result["city"], "Москва")
        self.assertEqual(result["temperature"], 18)
        self.assertEqual(result["description"], "облачно")
        self.assertIn("18°C", result["summary"])

    @patch.dict("core.services.weather.os.environ", {}, clear=True)
    def test_weather_service_requires_openweathermap_key(self):
        with self.assertRaisesMessage(
            ValueError,
            "OPENWEATHERMAP_API_KEY не задан",
        ):
            get_current_weather("Москва")

    @patch("core.services.forecast.requests.get")
    @patch.dict(
        "core.services.forecast.os.environ",
        {"OPENWEATHERMAP_API_KEY": "test-key"},
    )
    def test_forecast_service_groups_points_by_day(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "city": {"name": "Москва"},
                "list": [
                    {
                        "dt_txt": "2026-05-08 12:00:00",
                        "main": {"temp": 10.2},
                        "weather": [{"description": "дождь"}],
                    },
                    {
                        "dt_txt": "2026-05-08 15:00:00",
                        "main": {"temp": 12.6},
                        "weather": [{"description": "ясно"}],
                    },
                    {
                        "dt_txt": "2026-05-09 12:00:00",
                        "main": {"temp": 14.1},
                        "weather": [{"description": "облачно"}],
                    },
                ],
            },
        )

        result = get_five_day_forecast("Москва")

        self.assertEqual(result["city"], "Москва")
        self.assertEqual(len(result["days"]), 2)
        self.assertEqual(result["days"][0]["date"], "2026-05-08")
        self.assertEqual(result["days"][0]["min_temp"], 10)
        self.assertEqual(result["days"][0]["max_temp"], 13)

    @patch.dict("core.services.forecast.os.environ", {}, clear=True)
    def test_forecast_service_requires_openweathermap_key(self):
        with self.assertRaisesMessage(
            ValueError,
            "OPENWEATHERMAP_API_KEY не задан",
        ):
            get_five_day_forecast("Москва")

    @patch("core.services.currency.requests.get")
    def test_currency_service_parses_cbr_xml(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            content=b"""<?xml version="1.0" encoding="windows-1251"?>
            <ValCurs>
                <Valute>
                    <CharCode>USD</CharCode>
                    <Nominal>1</Nominal>
                    <Name>Dollar</Name>
                    <Value>81,45</Value>
                </Valute>
            </ValCurs>""",
        )

        result = get_currency_rate("usd")

        self.assertEqual(result["code"], "USD")
        self.assertEqual(result["nominal"], 1)
        self.assertEqual(result["rate"], 81.45)
        self.assertEqual(result["summary"], "1 USD = 81.45 RUB")

    @patch("core.services.news.requests.get")
    def test_news_service_parses_lenta_links(self, mock_get):
        html = """
        <html><body>
            <a class="card-mini" href="/news/2026/05/08/one/">
                Первая новость
            </a>
            <a
                class="card-mini"
                href="https://lenta.ru/news/2026/05/08/two/"
            >
                Вторая новость
            </a>
        </body></html>
        """
        mock_get.return_value = Mock(status_code=200, text=html)

        result = get_news(limit=2)

        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["title"], "Первая новость")
        self.assertEqual(
            result["items"][0]["url"],
            "https://lenta.ru/news/2026/05/08/one/",
        )
