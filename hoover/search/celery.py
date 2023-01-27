# from https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html
import os

from opentelemetry.instrumentation.celery import CeleryInstrumentor
from celery import Celery
from celery.signals import worker_process_init

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hoover.site.settings.docker_local')


@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    CeleryInstrumentor().instrument()


app = Celery('search')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
