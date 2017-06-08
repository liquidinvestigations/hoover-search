from django.core.management.base import BaseCommand
from ...models import Collection
from ...crawl import crawl_collection, reset_crawl

class Command(BaseCommand):

    help = "Crawl a collection"

    def add_arguments(self, parser):
        parser.add_argument('collection')
        parser.add_argument('--reset', action='store_true')

    def handle(self, verbosity, collection, reset, **options):
        col = Collection.objects.get(name=collection)
        if reset:
            reset_crawl(col)
        crawl_collection(col)
