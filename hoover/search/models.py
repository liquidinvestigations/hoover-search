import uuid
from datetime import timedelta
import logging

from cachetools import cached, TTLCache
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from . import es
from .loaders.external import Loader as ExternalLoader


log = logging.getLogger(__name__)
User = get_user_model()


@cached(cache=TTLCache(maxsize=128, ttl=59))
def _get_collection_loader(name):
    return ExternalLoader(url=settings.SNOOP_BASE_URL + f'/collections/{name}/json')


class Collection(models.Model):
    UPDATE_INTERVAL_SEC = 100
    SEARCH_OVERHEAD = 0.001

    title = models.CharField(max_length=2048, blank=True)
    name = models.CharField(max_length=256, unique=True)
    index = models.CharField(max_length=256)

    public = models.BooleanField(default=False)
    writeable = models.BooleanField(default=False)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                   related_name='hoover_search_collections')
    groups = models.ManyToManyField('auth.Group', blank=True,
                                    related_name='hoover_search_collections')
    uploader_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                            related_name='hoover_search_upload_collections')
    uploader_groups = models.ManyToManyField('auth.Group', blank=True,
                                             related_name='hoover_search_upload_collections')

    doc_count = models.IntegerField(default=0)
    avg_search_time = models.FloatField(default=0)
    avg_batch_time = models.FloatField(default=0)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_loader(self):
        return _get_collection_loader(self.name)

    def get_meta(self):
        return self.get_loader().api.meta

    def label(self):
        return self.title or self.name

    @classmethod
    def objects_for_user(cls, user):
        rv = set(cls.objects.filter(public=True))
        if user.id is not None:
            for group in user.groups.all():
                rv |= set(group.hoover_search_collections.all())
            rv |= set(cls.objects.filter(users__id=user.id))
        return rv

    @property
    def count(self):
        return self.doc_count

    @property
    def search_time(self):
        return (self.avg_search_time
                + settings.DEBUG_WAIT_PER_COLLECTION * Collection.objects.all().count())

    @property
    def batch_count_time(self):
        return (self.avg_batch_time
                + settings.DEBUG_WAIT_PER_COLLECTION * Collection.objects.all().count())

    def _get_avg_search_time(self):
        # value used to avoid division by 0 when doing document count arithmethic. Used to soften out
        # fractions for low document counts. For collections under this count, result times do not matter
        # that much.
        C_docs = 1000
        new_cached_entries = (
            self.searchresultcache_set
            .exclude(date_started__isnull=True)
            .exclude(date_finished__isnull=True)
            .exclude(result__isnull=True)
            .filter(date_finished__gt=timezone.now() - timedelta(seconds=self.UPDATE_INTERVAL_SEC) * 2)
            .annotate(duration=models.F('date_finished') - models.F('date_started'))
        )

        entry_count = 0
        total_time = 0
        for item in new_cached_entries:
            entry_count += 1
            total_doc_count = item.collections.aggregate(count=models.Sum('doc_count'))['count'] or 0
            total_time += item.duration.total_seconds() * \
                float(C_docs + self.doc_count) / float(C_docs + total_doc_count)
            log.warning("search %s %s %s", item.duration.total_seconds(), self.doc_count, total_doc_count)

        if not entry_count:
            # abort if nothing new
            return None

        # include old search time into new average; assume past searches count up for this many searches
        C_past = 3
        total_time += self.avg_search_time * C_past
        entry_count += C_past
        return (round(total_time / entry_count + self.SEARCH_OVERHEAD, 4)
                + settings.DEBUG_WAIT_PER_COLLECTION * Collection.objects.all().count())

    def _get_avg_batch_time(self):
        # value used to avoid division by 0 when doing document count arithmethic. Used to soften out
        # fractions for low document counts. For collections under this count, result times do not matter
        # that much.
        C_docs = 1000
        new_cached_entries = (
            self.batchresultcache_set
            .exclude(date_started__isnull=True)
            .exclude(date_finished__isnull=True)
            .exclude(result__isnull=True)
            .filter(date_finished__gt=timezone.now() - timedelta(seconds=self.UPDATE_INTERVAL_SEC) * 2)
            .annotate(duration=models.F('date_finished') - models.F('date_started'))
        )

        entry_count = 0
        total_time = 0
        for item in new_cached_entries:
            entry_count += 1
            total_doc_count = item.collections.aggregate(count=models.Sum('doc_count'))['count'] or 0
            total_time += item.duration.total_seconds() * \
                float(C_docs + self.doc_count) / float(C_docs + total_doc_count) * \
                (1.0 / (1 + len(item.args.get('query_strings', []))))
            log.warning("batch %s %s %s", item.duration.total_seconds(), self.doc_count, total_doc_count)

        if not entry_count:
            # abort if nothing new
            return None

        # include old search time into new average; assume past searches count up for this many searches
        C_past = 3
        total_time += self.avg_search_time * C_past
        entry_count += C_past
        return (round(total_time / entry_count + self.SEARCH_OVERHEAD, 5)
                + settings.DEBUG_WAIT_PER_COLLECTION * Collection.objects.all().count())

    def update(self):
        # early exit if already updated
        if (timezone.now() - self.last_update).total_seconds() <= self.UPDATE_INTERVAL_SEC:
            return

        # compute new ES index size
        try:
            self.doc_count = es.count(self.id)
        except Exception as e:
            log.exception(e)

        # compute new average search time
        new_time = self._get_avg_search_time()
        if new_time:
            self.avg_search_time = new_time
        new_time = self._get_avg_batch_time()
        if new_time:
            self.avg_batch_time = new_time

        # update timestamp and save
        self.last_update = timezone.now()
        self.save()

    def user_access_list(self):
        return ', '.join(u.username for u in self.users.all())

    def uploaders_access_list(self):
        return ', '.join(u.username for u in self.uploader_users.all() & self.users.all())

    def group_access_list(self):
        return ', '.join(g.name for g in self.groups.all())

    def group_upload_access_list(self):
        return ', '.join(g.name for g in self.uploader_groups.all() & self.groups.all())

    def get_document(self, doc_id):
        return es.get(self.id, doc_id)


def random_uuid():
    return str(uuid.uuid4())


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=50, default=random_uuid)
    preferences = models.JSONField(default=dict)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    p, _ = Profile.objects.get_or_create(user=instance)
    p.save()


class SearchResultCache(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    args = models.JSONField()
    collections = models.ManyToManyField(Collection)
    result = models.JSONField(null=True, default=None)
    task_id = models.CharField(max_length=51, unique=True, default=random_uuid)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_started = models.DateTimeField(null=True)
    date_finished = models.DateTimeField(null=True)

    def to_dict(self):
        """Returns a dict that can be serialized to JSON."""
        return {
            "user": self.user.username,
            "args": self.args,
            "collections": [c.name for c in self.collections.all()],
            "task_id": self.task_id,

            "date_created": self.date_created,
            "date_modified": self.date_modified,
            "date_started": self.date_started,
            "date_finished": self.date_finished,

            'status': 'done' if self.date_finished else ('running' if self.date_started else 'pending'),

            "result": self.result,

            "eta": self._get_eta(),
        }

    def _get_eta(self):
        def search_time(x):
            return (sum(c.search_time for c in x.collections.all()) * 1.5
                    + settings.DEBUG_WAIT_PER_COLLECTION * Collection.objects.all().count())

        own_search_time = 1 + round(search_time(self), 1)
        res = {}

        if not self.date_finished:
            # consider only the unfinished tasks created at most 5s after self
            others = SearchResultCache.objects.filter(
                date_finished__isnull=True,
                date_created__lt=self.date_created + timedelta(seconds=5),
            ).exclude(task_id=self.task_id)

            queue_len = len(others)
            others_search_time = sum(search_time(x) for x in others) / settings.SEARCH_WORKER_COUNT

            # if we're the only task, that means we aren't taking into account at least one more task,
            # so let's increase ETA by 50%
            if others_search_time < 1:
                own_search_time = 1 + int(own_search_time * 1.5)

            res['total_sec'] = int(own_search_time + others_search_time)
            res['own_search_sec'] = int(own_search_time)
            res['queue_sec'] = int(others_search_time)
            res['queue_length'] = queue_len
        return res


class BatchResultCache(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    args = models.JSONField()
    collections = models.ManyToManyField(Collection)
    result = models.JSONField(null=True, default=None)
    task_id = models.CharField(max_length=51, unique=True, default=random_uuid)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_started = models.DateTimeField(null=True)
    date_finished = models.DateTimeField(null=True)

    def to_dict(self):
        """Returns a dict that can be serialized to JSON."""
        return {
            "user": self.user.username,
            "args": self.args,
            "collections": [c.name for c in self.collections.all()],
            "task_id": self.task_id,

            "date_created": self.date_created,
            "date_modified": self.date_modified,
            "date_started": self.date_started,
            "date_finished": self.date_finished,

            'status': 'done' if self.date_finished else ('running' if self.date_started else 'pending'),

            "result": self.result,

            "eta": self._get_eta(),
        }

    def _get_eta(self):
        def batch_count_time(x):
            return (sum(c.batch_count_time for c in x.collections.all())
                    * (1 + len(x.args.get('query_strings', [])))
                    + settings.DEBUG_WAIT_PER_COLLECTION * Collection.objects.all().count())

        own_search_time = 1 + round(batch_count_time(self), 1)
        res = {}

        if not self.date_finished:
            # consider only the unfinished tasks created at most 5s after self
            others = BatchResultCache.objects.filter(
                date_finished__isnull=True,
                date_created__lt=self.date_created + timedelta(seconds=5),
            ).exclude(task_id=self.task_id)

            queue_len = len(others)
            others_search_time = sum(batch_count_time(x) for x in others) / settings.SEARCH_WORKER_COUNT

            # if we're the only task, that means we aren't taking into account at least one more task,
            # so let's increase ETA by 50%
            if others_search_time < 1:
                own_search_time = 1 + int(own_search_time * 1.5)

            res['total_sec'] = int(own_search_time + others_search_time)
            res['own_search_sec'] = int(own_search_time)
            res['queue_sec'] = int(others_search_time)
            res['queue_length'] = queue_len
        return res


class Upload(models.Model):
    """Database model to keep track of user uploads."""

    started = models.DateTimeField(auto_now_add=True)
    """Timestamp when the upload started."""

    finished = models.DateTimeField(null=True, blank=True)
    """Timestamp when the upload finished."""

    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
    """Reference to the user who is uploading."""

    collection = models.ForeignKey(Collection)
    """Reference to the collection in which the file is being uploaded."""

    directory_id = models.IntegerField()
    """The directory id that corresponds to the directory the file is being uploaded to."""

    filename = models.CharField(max_length=256)
    """The filename of the uploaded file."""
