from ...signals import sync_nextcloud_collections
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync nextcloud collections with snoop"

    def handle(self, *args, **options):
        sync_nextcloud_collections()
