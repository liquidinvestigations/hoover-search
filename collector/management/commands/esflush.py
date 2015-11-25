from django.core.management.base import BaseCommand
from ... import es


class Command(BaseCommand):

    help = "Imprt configuration file"

    def handle(self, verbosity, **options):
        es.flush()
