from django.core.management.base import BaseCommand
from ...models import Collection
from ...crawl import crawl_collection

class Command(BaseCommand):

    help = "Crawl a collection"

    def add_arguments(self, parser):
        parser.add_argument('collection')

    def handle(self, verbosity, collection, **options):
        crawl_collection(Collection.objects.get(name=collection))
