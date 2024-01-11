from time import sleep
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_celery_results.models import TaskResult

from hoover.search.views import SEARCH_CACHE_AGE, BATCH_CACHE_AGE, SEARCH_KEY, BATCH_KEY
from hoover.search import models


log = logging.getLogger(__name__)


def delete_old_search_cache_entries():
    log.warning('deleting old search cache...')
    delete_before = timezone.now() - SEARCH_CACHE_AGE
    models.SearchResultCache.objects.filter(date_created__lt=delete_before).delete()
    TaskResult.objects.filter(
        date_created__lt=delete_before,
        task_name=SEARCH_KEY,
    ).delete()


def delete_old_batch_cache_entries():
    log.warning('deleting old batch search cache...')
    delete_before = timezone.now() - BATCH_CACHE_AGE
    models.BatchResultCache.objects.filter(date_created__lt=delete_before).delete()
    TaskResult.objects.filter(
        date_created__lt=delete_before,
        task_name=BATCH_KEY,
    ).delete()


def run_single_update_step():
    try:
        delete_old_batch_cache_entries()
        for _ in range(30):
            log.warning('starting collection stats update...')
            for c in models.Collection.objects.all():
                c.update()
            delete_old_search_cache_entries()
            sleep(models.Collection.UPDATE_INTERVAL_SEC)
    except Exception as e:
        log.warning('failed while running updates!')
        log.exception(e)
        sleep(models.Collection.UPDATE_INTERVAL_SEC)


class Command(BaseCommand):
    help = "Continuously update the collection search statistics every minute."""

    def handle(self, **kwargs):
        while True:
            run_single_update_step()
