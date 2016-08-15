from django.core.management.base import BaseCommand
from ...models import Collection
from ...es import list_indices, delete


class Command(BaseCommand):

    help = "Delete extra elasticsearch indices"

    def handle(self, **options):
        for collection_id in list_indices():
            try:
                Collection.objects.get(id=collection_id)
            except Collection.DoesNotExist:
                print('deleting', collection_id)
                delete(collection_id)
