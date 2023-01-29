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

    loglevel = 'info' if settings.DEBUG else 'error'
    return [
        celery_binary,
        '-A', 'hoover.search',
        'worker',
        '-E',
        '--pidfile=',
        f'--loglevel={loglevel}',
        '-Ofair',
        '--max-memory-per-child', str(500),
        # '--max-tasks-per-child', str(1),
        '--prefetch-multiplier', str(1),
        '--soft-time-limit', '3600',  # 1h
        '--time-limit', '4000',
        '-Q', ','.join(queues),
        '-c', str(settings.SEARCH_WORKER_COUNT),
        '--pool', 'prefork',
        # '--pool', 'solo',
    ]


class Command(BaseCommand):
    help = "Run one search worker in this container."""

    def add_arguments(self, parser):
        parser.add_argument('worker_type')

    def handle(self, worker_type, **kwargs):
        if worker_type == 'search':
            argv = celery_argv(settings.HOOVER_CELERY_SEARCH_QUEUES)
        elif worker_type == 'batch':
            argv = celery_argv(settings.HOOVER_CELERY_BATCH_QUEUES)
        else:
            raise RuntimeError('bad worker_type (valid: batch, search)')

        print('+' + ' '.join(argv))
        os.execv(argv[0], argv)
