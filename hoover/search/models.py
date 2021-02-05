import uuid
import logging

from django.db import models
from django.conf import settings
from cachetools import cached, TTLCache
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from . import es
from .loaders.external import Loader as ExternalLoader


log = logging.getLogger(__name__)
User = get_user_model()


@cached(cache=TTLCache(maxsize=128, ttl=59))
def _get_collection_loader(name):
    return ExternalLoader(url=settings.SNOOP_BASE_URL + f'/collections/{name}/json')


class Collection(models.Model):

    title = models.CharField(max_length=2048, blank=True)
    name = models.CharField(max_length=256, unique=True)
    index = models.CharField(max_length=256)

    public = models.BooleanField(default=False)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                   related_name='hoover_search_collections')
    groups = models.ManyToManyField('auth.Group', blank=True,
                                    related_name='hoover_search_collections')

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

    def count(self):
        try:
            return es.count(self.id)
        except Exception as e:
            log.exception(e)
            return -1

    def user_access_list(self):
        return ', '.join(u.username for u in self.users.all())

    def group_access_list(self):
        return ', '.join(g.name for g in self.groups.all())

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
