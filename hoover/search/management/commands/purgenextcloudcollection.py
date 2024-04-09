import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from ... import models


class Command(BaseCommand):
    help = "Remove a nextcloud collection"

    def add_arguments(self, parser):
        parser.add_argument('collection_name')

    def handle(self, collection_name, **kwargs):

        nextcloud_collection = models.NextcloudCollection.objects.filter(name=collection_name).first()
        if not nextcloud_collection:
            print(f'Nextcloud collection not found: {collection_name}')
            return

        collection = nextcloud_collection.collection
        nextcloud_collection.delete()
        collection.delete()
        print(f'Deleted nextcloud collection and corresponding collection from database: {collection_name}')

        snoop_base_url = settings.SNOOP_BASE_URL
        assert snoop_base_url

        url = snoop_base_url + f'/common/remove-nextcloud-collection/{collection_name}'
        res = requests.get(url)

        if res.status_code == 200:
            print('Deleted nextcloud collection from snoop database.')
        elif res.status_code == 404:
            print(f'Nextcloud collection not found in snoop database: {collection_name}')
        else:
            print(f'Unknown response from snoop: {res}')
