import time
from django.core.management.base import BaseCommand
from ...models import Collection
from ...index import update_collection, logger as index_logger
from ...loaders.collectible import logger as collectible_logger
from ...utils import LOG_LEVEL


class Command(BaseCommand):

    help = "Import a collection"

    def add_arguments(self, parser):
        parser.add_argument('collection')
        parser.add_argument('-s', '--sleep', type=int)

    def handle(self, verbosity, collection, sleep, **options):
        index_logger.setLevel(LOG_LEVEL[verbosity])
        collectible_logger.setLevel(LOG_LEVEL[verbosity])

        while True:
            report = update_collection(Collection.objects.get(name=collection))
            count = report.get('indexed', 0)
            print('indexed {} documents'.format(count))
            if count and sleep:
                print('waiting {}s ...'.format(sleep))
                time.sleep(sleep)
            else:
                print('done')
                break
