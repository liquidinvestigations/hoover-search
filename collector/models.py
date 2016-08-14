import hashlib
import json
from django.db import models
from django.db.models import Q
from django.dispatch import receiver
from django.conf import settings
from django.utils.module_loading import import_string
from . import es


class Collection(models.Model):

    title = models.CharField(max_length=2048, blank=True)
    name = models.CharField(max_length=256, unique=True)
    index = models.CharField(max_length=256)

    public = models.BooleanField(default=False)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    loader = models.CharField(max_length=2048,
        default='collector.loaders.upload.Loader')
    options = models.TextField(default='{}')

    def __unicode__(self):
        return self.name

    def get_loader(self):
        cls = import_string(self.loader)
        return cls(self, **json.loads(self.options))

    def label(self):
        return self.title or self.name

    @classmethod
    def objects_for_user(cls, user):
        query = Q(public=True)
        if user.id is not None:
            query = query | Q(users__id=user.id)
        return cls.objects.filter(query)

    def count(self):
        return es.count(self.id)

    def access_list(self):
        return ', '.join(u.username for u in self.users.all())

    def set_mapping(self):
        loader = self.get_loader()
        fields = loader.get_metadata().get('fields', {})
        fields.setdefault('id', {'type': 'string', 'not_analyzed': True})
        es.set_mapping(self.id, fields)

    def reset(self):
        es.delete_index(self.id, ok_missing=True)
        es.create_index(self.id, self.name)
        self.set_mapping()

    def get_document(self, doc_id):
        return es.get(self.id, doc_id)
