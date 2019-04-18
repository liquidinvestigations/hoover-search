from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "List existing collections"

    def handle(self, **kwargs):
        collections = models.Collection.objects.all()
        for collection in collections:
            print(collection.name)
