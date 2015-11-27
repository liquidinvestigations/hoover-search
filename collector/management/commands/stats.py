from django.core.management.base import BaseCommand
from ...es import stats


class Command(BaseCommand):

    help = "Imprt configuration file"

    def handle(self, **options):
        from pprint import pprint
        pprint(stats())
