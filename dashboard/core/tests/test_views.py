from pathlib import Path
from unittest.mock import patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings

from core.middleware import RequestLogMiddleware
from core.views import (
    currency_view,
    forecast_view,
    home,
    news_view,
    weather_view,
)


class ViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_home_view_renders_section_cards(self):
        response = home(self._request("/"))
        content = response.content.decode("utf-8")

        self.assertIn("Текущая погода", content)
        self.assertIn("Прогноз на 5 дней", content)
        self.assertIn("Курс валют", content)
        self.assertIn("Новости", content)
        self.assertIn("/weather/?city=Москва", content)
        self.assertIn("/forecast/?city=Москва", content)
        self.assertIn("/currency/?code=USD", content)
        self.assertIn("/news/", content)

    @patch("core.views.get_current_weather")
    def test_weather_view_renders_weather_and_logs_request(self, mock_weather):
        mock_weather.return_value = {
            "city": "Москва",
            "temperature": 18,
            "description": "облачно",
            "feels_like": 17,
            "humidity": 61,
            "wind_speed": 3.5,
            "summary": "18°C, облачно",
        }
        logs_dir = Path(self.tmpdir)

        with override_settings(LOGS_DIR=logs_dir):
            request = self._request("/weather/?city=Москва")
            response = RequestLogMiddleware(weather_view)(request)

        content = response.content.decode("utf-8")
        self.assertIn("Москва", content)
        self.assertIn("18°C", content)
        log_files = list(logs_dir.glob("*.log"))
        self.assertEqual(len(log_files), 1)
        log_text = log_files[0].read_text(encoding="utf-8")
        self.assertIn("GET /weather/?city=", log_text)
        self.assertIn("Результат: 18°C, облачно", log_text)

    @patch("core.views.get_current_weather")
    def test_weather_view_renders_service_error_without_traceback(
        self,
        mock_weather,
    ):
        mock_weather.side_effect = ValueError(
            "OPENWEATHERMAP_API_KEY не задан"
        )
        logs_dir = Path(self.tmpdir)

        with override_settings(LOGS_DIR=logs_dir):
            request = self._request("/weather/?city=Москва")
            response = RequestLogMiddleware(weather_view)(request)

        content = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("OPENWEATHERMAP_API_KEY не задан", content)
        log_text = next(logs_dir.glob("*.log")).read_text(encoding="utf-8")
        self.assertIn(
            "Результат: ошибка: OPENWEATHERMAP_API_KEY не задан",
            log_text,
        )

    @patch("core.views.get_five_day_forecast")
    def test_forecast_view_renders_forecast(self, mock_forecast):
        mock_forecast.return_value = {
            "city": "Москва",
            "days": [
                {
                    "date": "2026-05-08",
                    "min_temp": 10,
                    "max_temp": 13,
                    "description": "ясно",
                }
            ],
            "summary": "прогноз на 5 дней получен",
        }

        response = forecast_view(self._request("/forecast/?city=Москва"))
        content = response.content.decode("utf-8")

        self.assertIn("2026-05-08", content)
        self.assertIn("ясно", content)

    @patch("core.views.get_five_day_forecast")
    def test_forecast_view_renders_service_error_without_traceback(
        self,
        mock_forecast,
    ):
        mock_forecast.side_effect = ValueError(
            "OPENWEATHERMAP_API_KEY не задан"
        )
        logs_dir = Path(self.tmpdir)

        with override_settings(LOGS_DIR=logs_dir):
            request = self._request("/forecast/?city=Москва")
            response = RequestLogMiddleware(forecast_view)(request)

        content = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("OPENWEATHERMAP_API_KEY не задан", content)
        log_text = next(logs_dir.glob("*.log")).read_text(encoding="utf-8")
        self.assertIn(
            "Результат: ошибка: OPENWEATHERMAP_API_KEY не задан",
            log_text,
        )

    @patch("core.views.get_currency_rate")
    def test_currency_view_renders_currency(self, mock_currency):
        mock_currency.return_value = {
            "code": "USD",
            "nominal": 1,
            "rate": 81.45,
            "name": "Dollar",
            "summary": "1 USD = 81.45 RUB",
        }

        response = currency_view(self._request("/currency/?code=USD"))

        self.assertIn("1 USD = 81.45 RUB", response.content.decode("utf-8"))

    @patch("core.views.get_news")
    def test_news_view_renders_news(self, mock_news):
        mock_news.return_value = {
            "items": [
                {
                    "title": "Первая новость",
                    "url": "https://lenta.ru/news/one/",
                }
            ],
            "summary": "1 новостей загружено",
        }

        response = news_view(self._request("/news/"))

        self.assertIn("Первая новость", response.content.decode("utf-8"))

    @property
    def tmpdir(self):
        import tempfile

        return tempfile.mkdtemp()

    def _request(self, path):
        request = self.factory.get(path)
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        return request
