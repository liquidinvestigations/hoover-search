import json
from django.core.management.base import BaseCommand
from django.conf import settings
from ... import models


class Command(BaseCommand):

    help = "Register a collection"

    def add_arguments(self, parser):
        parser.add_argument('snoop_collections')

    def handle(self, snoop_collections, **kwargs):
        snoop_base_url = settings.SNOOP_BASE_URL
        assert snoop_base_url

        for conf in json.loads(snoop_collections):
            name = conf['name']
            col, created = models.Collection.objects.update_or_create(
                name=name,
                defaults=dict(
                    title=name.title(),
                    index=name,
                    public=conf.get('public', True),
                ),
            )
            action = "Created" if created else "Updated"
            print(action, col)
