from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'hoover.search'

    def ready(self):
        from . import signals  # noqa: F401
