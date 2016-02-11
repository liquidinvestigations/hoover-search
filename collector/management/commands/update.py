from django.core.management.base import BaseCommand
from ...models import Collection
from ...index import update_collection, logger as index_logger
from ...loaders.collectible import logger as collectible_logger
from ...utils import LOG_LEVEL


class Command(BaseCommand):

    help = "Imprt configuration file"

    def add_arguments(self, parser):
        parser.add_argument('collection')
        parser.add_argument('--threads', default=1, type=int)

    def handle(self, verbosity, collection, threads, **options):
        index_logger.setLevel(LOG_LEVEL[verbosity])
        collectible_logger.setLevel(LOG_LEVEL[verbosity])
        update_collection(Collection.objects.get(name=collection), threads)
