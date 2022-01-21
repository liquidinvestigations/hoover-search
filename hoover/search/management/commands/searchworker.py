import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand


def celery_argv(queues):
    celery_binary = (
        subprocess.check_output(['which', 'celery'])
        .decode('latin1')
        .strip()
    )

    loglevel = 'warning' if settings.DEBUG else 'error'
    return [
        celery_binary,
        '-A', 'hoover.search',
        'worker',
        '-E',
        '--pidfile=',
        f'--loglevel={loglevel}',
        '-Ofair',
        '--max-memory-per-child', str(500),
        '--soft-time-limit', '3600',  # 1h
        '--time-limit', '4000',
        '-Q', ','.join(queues),
        '-c', str(settings.SEARCH_WORKER_COUNT),
    ]


class Command(BaseCommand):
    help = "Run one search worker in this container."""

    def handle(self, **kwargs):
        argv = celery_argv(settings.HOOVER_CELERY_SEARCH_QUEUES)
        print('+' + ' '.join(argv))
        os.execv(argv[0], argv)
