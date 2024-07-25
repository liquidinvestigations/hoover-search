from django.core.management.base import BaseCommand
from datetime import datetime
from django.contrib.auth.models import User
from ...models import NextcloudCollection, NextcloudDirectory, WebDAVPassword, Collection
from ...tasks import WEBDAV_LOCATION_SUFFIX

DEMO_COLLECTION_NAME = 'demo'
DEMO_COLLECTION_USER = 'demo'


class Command(BaseCommand):
    help = "Setup the demo mode and create necessary database entries."

    def add_arguments(self, parser):
        parser.add_argument('webdav_password')

    def handle(self, *args, **options):
        webdav_password = options['webdav_password']
        try:
            demo_user = User.objects.get(username=DEMO_COLLECTION_USER)
        except User.DoesNotExist:
            demo_user = User.objects.create_user(DEMO_COLLECTION_USER)

            WebDAVPassword.objects.get_or_create(password=webdav_password,
                                                 user=demo_user)

        directory, _ = NextcloudDirectory.objects.get_or_create(
            # username and directory name
            path=WEBDAV_LOCATION_SUFFIX +
            f'/{DEMO_COLLECTION_USER}/{DEMO_COLLECTION_NAME}',
            defaults={
                'name': DEMO_COLLECTION_NAME,
                'user': demo_user,
                'deleted_from_nextcloud': None,
                'modified': datetime.now()
            })
        print('making collection')
        collection, _ = Collection.objects.get_or_create(
            name=DEMO_COLLECTION_NAME,
            title=DEMO_COLLECTION_NAME,
            index=DEMO_COLLECTION_NAME,
            public=True)
        print('making nextcloud collection')
        nextcloud_collection, _ = NextcloudCollection.objects.get_or_create(
            name=DEMO_COLLECTION_NAME,
            directory=directory,
            collection=collection)
