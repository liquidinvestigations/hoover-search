import json
from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "Set collection title"

    def add_arguments(self, parser):
        parser.add_argument('name')
        parser.add_argument('title')

    def handle(self, name, title, **kwargs):
        collection = models.Collection.objects.get(name=name)
        collection.title = title
        collection.save()
