from django.db import models
from django.conf import settings

class Collection(models.Model):

    title = models.CharField(max_length=2048, blank=True)
    name = models.CharField(max_length=256, unique=True)
    index = models.CharField(max_length=256)

    public = models.BooleanField(default=False)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
        related_name='hoover_search_collections')

    loader = models.CharField(max_length=2048,
        default='collector.loaders.upload.Loader')
    options = models.TextField(default='{}')
