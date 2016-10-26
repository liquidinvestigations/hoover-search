import json
from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "Register a new collection"

    def add_arguments(self, parser):
        parser.add_argument('name')
        parser.add_argument('--index')
        parser.add_argument('--loader')
        parser.add_argument('--options')

    def handle(self, name, index, loader, options, **kwargs):
        json.loads(options or '{}')  # make sure it's valid json
        models.Collection.objects.create(
            title=name.title(),
            name=name,
            index=index or name,
            loader=loader or 'hoover.search.loaders.upload.Loader',
            options=options or '{}',
        )
