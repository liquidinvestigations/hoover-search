from django.core.management.base import BaseCommand
from ...models import Collection
from ...index import update_collection, logger
from ...utils import LOG_LEVEL


class Command(BaseCommand):

    help = "Imprt configuration file"

    def add_arguments(self, parser):
        parser.add_argument('collection')

    def handle(self, verbosity, collection, **options):
        logger.setLevel(LOG_LEVEL[verbosity])
        update_collection(Collection.objects.get(slug=collection))
