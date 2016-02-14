from django.core.management.base import BaseCommand
from ...es import status


class Command(BaseCommand):

    help = "Show elasticsearch status"

    def handle(self, **options):
        from pprint import pprint
        pprint(status())
