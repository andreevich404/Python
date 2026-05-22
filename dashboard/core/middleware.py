from datetime import datetime
from pathlib import Path

from django.conf import settings


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.session_key:
            request.session.create()

        response = self.get_response(request)
        self._write_log(request, response)
        return response

    def _write_log(self, request, response):
        logs_dir = Path(settings.LOGS_DIR)
        logs_dir.mkdir(parents=True, exist_ok=True)

        result = getattr(request, "dashboard_result", "-")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = (
            f"{response.status_code} "
            f"{getattr(response, 'reason_phrase', '')}"
        ).strip()
        line = (
            f"[{timestamp}] {request.method} {request.get_full_path()} -> "
            f"{status} | Результат: {result}\n"
        )
        user_id = request.session.get("user_id") or request.session.session_key
        user_name = request.session.get("user_name", "anonymous")
        line = line.rstrip("\n") + f" | Пользователь: {user_name}\n"
        log_path = logs_dir / f"{user_id}.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(line)
