from time import time
from django.db import models, IntegrityError, transaction


class Count(models.Model):

    key = models.CharField(max_length=200, primary_key=True)
    n = models.IntegerField(default=0)
    expires = models.IntegerField()

    @classmethod
    def open(cls, key, interval, lock):
        t0 = interval * int(time() / interval)
        t1 = t0 + interval
        cls.objects.get_or_create(key=key, defaults={'expires': t1})

        query = cls.objects
        if lock:
            query = query.select_for_update()

        counter = query.get(key=key)

        if counter.expires <= t0:
            counter.expires = t1
            counter.n = 0

        return counter

    @classmethod
    @transaction.atomic
    def inc(cls, key, interval):
        counter = cls.open(key, interval, lock=True)
        counter.n += 1
        counter.save()
        return counter.n

    @classmethod
    def get(cls, key, interval):
        counter = cls.open(key, interval, lock=False)
        return counter.n
