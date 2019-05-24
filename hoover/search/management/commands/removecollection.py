from django.core.management.base import BaseCommand
from ... import models
from hoover.search.es import delete_index

class Command(BaseCommand):

    help = "Remove a collection"

    def add_arguments(self, parser):
        parser.add_argument('name')

    def handle(self, name, **kwargs):
        collection = models.Collection.objects.get(name=name)
        delete_index(collection.id, ok_missing=True)
        collection.delete()
