from django.apps import AppConfig


class UploadConfig(AppConfig):
    name = 'hoover.upload'

    def ready(self):
        import hoover.upload.signals.handlers # noqa
