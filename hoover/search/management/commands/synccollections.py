import json
from django.core.management.base import BaseCommand
from django.conf import settings
from ... import models


class Command(BaseCommand):
    help = "Register a collection"

    def add_arguments(self, parser):
        parser.add_argument('snoop_collections_json')

    def handle(self, snoop_collections_json, **kwargs):
        snoop_base_url = settings.SNOOP_BASE_URL
        assert snoop_base_url

        snoop_collections = json.loads(snoop_collections_json)
        print('json string has', len(snoop_collections), 'collections')
        to_delete = models.Collection.objects.exclude(name__in=[c['name'] for c in snoop_collections])
        print('Deleting', to_delete.count(), 'collections')
        to_delete.delete()

        for conf in snoop_collections:
            name = conf['name']
            print('Handling collection', name)
            col, created = models.Collection.objects.update_or_create(
                name=name,
                defaults=dict(
                    index=name,
                ),
            )
            if created or not col.title:
                col.title = name
                col.save()

            action = "Created" if created else "Updated"
            print(action, col)
