import os
import sys
from django.core.asgi import get_asgi_application

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studiopilates.settings")
application = get_asgi_application()
