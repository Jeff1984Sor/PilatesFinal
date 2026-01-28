from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "studiopilates.core"

    def ready(self):
        from . import signals  # noqa: F401
        from .whatsapp_scheduler import start_scheduler  # noqa: F401

        start_scheduler()
