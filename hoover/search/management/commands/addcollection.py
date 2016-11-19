import json
from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "Register a collection"

    def add_arguments(self, parser):
        parser.add_argument('name')
        parser.add_argument('url')
        parser.add_argument('--index')

    def handle(self, name, url, index, **kwargs):
        models.Collection.objects.create(
            title=name.title(),
            name=name,
            index=index or name,
            loader='hoover.search.loaders.jsonapi.Loader',
            options=json.dumps({'url': url}),
        )
