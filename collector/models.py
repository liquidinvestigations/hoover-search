import hashlib
from django.db import models
from django.conf import settings


class Collection(models.Model):

    title = models.CharField(max_length=2048, blank=True)
    slug = models.CharField(max_length=256, unique=True)

    public = models.BooleanField(default=False)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    loader = models.CharField(max_length=2048,
        default='collector.loaders.collectible.Loader')
    options = models.TextField(default='{}')

    def __unicode__(self):
        return self.slug

    def label(self):
        return self.title or self.slug

    @classmethod
    def objects_for_user(cls, user):
        rv = set(cls.objects.filter(public=True))
        if user.id is not None:
            rv.update(cls.objects.filter(users__id=user.id))
        return rv


class Document(models.Model):

    slug = models.CharField(max_length=256, unique=True)
    title = models.CharField(max_length=2048, blank=True)
    url = models.URLField(max_length=2048)
    text_url = models.URLField(max_length=2048)
    indexed = models.BooleanField(default=False)
    index_time = models.DateTimeField(null=True, blank=True)

    collection = models.ForeignKey('Collection')

    def __unicode__(self):
        return self.slug
