import json
from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "Register a collection"

    def add_arguments(self, parser):
        parser.add_argument('name')
        parser.add_argument('url')
        parser.add_argument('--index')
        parser.add_argument('--public', action='store_true')

    def handle(self, name, url, index, public, **kwargs):
        models.Collection.objects.create(
            title=name.title(),
            name=name,
            index=index or name,
            public=public,
            loader='hoover.search.loaders.external.Loader',
            options=json.dumps({'url': url}),
        )
