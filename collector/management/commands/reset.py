from django.core.management.base import BaseCommand
from ...models import Collection
from ...utils import LOG_LEVEL


class Command(BaseCommand):

    help = "Delete and re-create the index for a collection"

    def add_arguments(self, parser):
        parser.add_argument('collection')

    def handle(self, verbosity, collection, **options):
        Collection.objects.get(name=collection).reset()
