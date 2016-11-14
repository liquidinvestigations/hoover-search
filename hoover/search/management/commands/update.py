from django.core.management.base import BaseCommand
from ...models import Collection
from ...index import update_collection, logger as index_logger
from ...loaders.collectible import logger as collectible_logger
from ...utils import LOG_LEVEL


class Command(BaseCommand):

    help = "Import a collection"

    def add_arguments(self, parser):
        parser.add_argument('collection')

    def handle(self, verbosity, collection, **options):
        index_logger.setLevel(LOG_LEVEL[verbosity])
        collectible_logger.setLevel(LOG_LEVEL[verbosity])
        update_collection(Collection.objects.get(name=collection))
