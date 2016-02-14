from django.core.management.base import BaseCommand
from ...es import stats


class Command(BaseCommand):

    help = "Show elasticsearch stats"

    def handle(self, **options):
        from pprint import pprint
        pprint(stats())
