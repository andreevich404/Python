import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard.settings")
application = get_wsgi_application()
