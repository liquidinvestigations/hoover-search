from django.db import models


class Document(models.Model):

    hash = models.CharField(max_length=300)
    url = models.URLField(max_length=2048)
    indexed = models.BooleanField(default=False)
    index_time = models.DateTimeField(null=True, blank=True)
