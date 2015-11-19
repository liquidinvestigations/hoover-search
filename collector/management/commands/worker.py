import threading
from django.core.management.base import BaseCommand
from ... import index


class Command(BaseCommand):

    help = "Run an indexing worker"

    def add_arguments(self, parser):
        parser.add_argument('--threads', default=1, type=int)

    def handle(self, verbosity, threads, **options):
        thread_list = [
            threading.Thread(target=index.work_loop)
            for _ in range(threads)
        ]

        for thread in thread_list:
            thread.start()

        for thread in thread_list:
            thread.join()
