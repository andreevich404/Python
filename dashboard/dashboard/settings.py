from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "semester-dashboard-dev-key"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "core",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.RequestLogMiddleware",
]

ROOT_URLCONF = "dashboard.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]
WSGI_APPLICATION = "dashboard.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Novokuznetsk"
USE_I18N = True
USE_TZ = False
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGS_DIR = BASE_DIR / "logs"
