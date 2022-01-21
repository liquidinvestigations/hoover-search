from time import sleep

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_celery_results.models import TaskResult

from hoover.search.views import SEARCH_CACHE_AGE
from hoover.search import models


def delete_old_search_cache_entries():
    delete_before = timezone.now() - SEARCH_CACHE_AGE

    models.SearchResultCache.objects.filter(date_created__lt=delete_before).delete()
    TaskResult.objects.filter(date_created__lt=delete_before).delete()


class Command(BaseCommand):
    help = "Continuously update the collection search statistics every minute."""

    def handle(self, **kwargs):
        while True:
            for c in models.Collection.objects.all():
                c.update()
            delete_old_search_cache_entries()
            sleep(models.Collection.UPDATE_INTERVAL_SEC)
