from django.core.management.base import BaseCommand
from ... import index


class Command(BaseCommand):

    help = "Run an indexing worker"

    def handle(self, verbosity, **options):
        index.work_loop()
