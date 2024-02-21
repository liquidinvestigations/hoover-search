from ...tasks import sync_nextcloud_directories
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync nextcloud directories."

    def handle(self, *args, **options):
        sync_nextcloud_directories(4, 50, purge=True)
