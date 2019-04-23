from django.apps import AppConfig


class UtilsConfig(AppConfig):
    name = "bing.utils"

    def ready(self):
        from . import checks  # noqa
