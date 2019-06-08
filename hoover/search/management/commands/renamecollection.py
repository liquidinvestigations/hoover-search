import json
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "Rename a collection"

    def add_arguments(self, parser):
        parser.add_argument('name')
        parser.add_argument('new_name')

    def handle(self, name, new_name, **kwargs):
        try:
            print(f'Rename "{name}" to "{new_name}"')
            collection = models.Collection.objects.get(name=name)
            collection.title = new_name.capitalize()
            collection.name = new_name
            collection.index = new_name.lower()
            collection.save()
        except ObjectDoesNotExist:
            print('Invalid collection name %s' % name)
            exit(1)
