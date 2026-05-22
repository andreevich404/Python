from pathlib import Path
from unittest.mock import patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings

from core.middleware import RequestLogMiddleware
from core.views import (
    details_view,
    forecast_view,
    home,
    identify,
    weather_news_view,
    weather_view,
)


class ViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_home_view_renders_name_input_before_dashboard(self):
        response = home(self._request("/"))
        content = response.content.decode("utf-8")

        self.assertIn("Имя пользователя", content)
        self.assertIn("weatherDashboardUserName", content)
        self.assertNotIn("Текущая погода", content)
        self.assertNotIn("/weather/?city=Москва", content)

    def test_home_view_renders_dashboard_after_identification(self):
        response = home(self._identified_request("/"))
        content = response.content.decode("utf-8")

        self.assertIn("Иван", content)
        self.assertNotIn(
            "Введите имя, чтобы история запросов сохранялась",
            content,
        )
        self.assertIn("Текущая погода", content)
        self.assertIn("Прогноз на 5 дней", content)
        self.assertIn("Детали погоды", content)
        self.assertIn("Новости погоды", content)
        self.assertIn("/weather/?city=Москва", content)
        self.assertIn("/forecast/?city=Москва", content)
        self.assertIn("/details/?city=Москва", content)
        self.assertIn("/weather-news/", content)

    def test_identify_view_saves_user_name_and_unique_id(self):
        request = self.factory.post("/identify/", {"user_name": "Иван"})
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()

        response = identify(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(request.session["user_name"], "Иван")
        self.assertEqual(len(request.session["user_id"]), 32)

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
            request.session["user_name"] = "Иван"
            request.session["user_id"] = "user-1"
            response = RequestLogMiddleware(weather_view)(request)

        content = response.content.decode("utf-8")
        self.assertIn("Москва", content)
        self.assertIn("18°C", content)
        log_files = list(logs_dir.glob("*.log"))
        self.assertEqual(len(log_files), 1)
        self.assertEqual(log_files[0].name, "user-1.log")
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
            request.session["user_name"] = "Иван"
            request.session["user_id"] = "user-1"
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

        response = forecast_view(self._identified_request(
            "/forecast/?city=Москва"
        ))
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
            request.session["user_name"] = "Иван"
            request.session["user_id"] = "user-1"
            response = RequestLogMiddleware(forecast_view)(request)

        content = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("OPENWEATHERMAP_API_KEY не задан", content)
        log_text = next(logs_dir.glob("*.log")).read_text(encoding="utf-8")
        self.assertIn(
            "Результат: ошибка: OPENWEATHERMAP_API_KEY не задан",
            log_text,
        )

    @patch("core.views.get_weather_details")
    def test_details_view_renders_scraped_weather_details(self, mock_details):
        mock_details.return_value = {
            "city": "Москва",
            "temperature": "+18",
            "wind": "4 м/с",
            "pressure": "755 мм рт. ст.",
            "summary": "детали погоды для Москва получены",
        }

        response = details_view(self._identified_request(
            "/details/?city=Москва"
        ))
        content = response.content.decode("utf-8")

        self.assertIn("+18", content)
        self.assertIn("4 м/с", content)

    @patch("core.views.get_weather_news")
    def test_weather_news_view_renders_scraped_news(self, mock_news):
        mock_news.return_value = {
            "items": [
                {
                    "title": "Сильный дождь придет вечером",
                    "url": "https://www.gismeteo.ru/news/weather-rain/",
                }
            ],
            "summary": "1 новостей погоды загружено",
        }

        response = weather_news_view(self._identified_request(
            "/weather-news/"
        ))

        self.assertIn(
            "Сильный дождь придет вечером",
            response.content.decode("utf-8"),
        )

    @property
    def tmpdir(self):
        import tempfile

        return tempfile.mkdtemp()

    def _request(self, path):
        request = self.factory.get(path)
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        return request

    def _identified_request(self, path):
        request = self._request(path)
        request.session["user_name"] = "Иван"
        request.session["user_id"] = "user-1"
        return request
