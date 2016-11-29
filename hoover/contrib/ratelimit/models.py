from time import time
from django.db import models, IntegrityError, transaction

class Count(models.Model):

    key = models.CharField(max_length=200, primary_key=True)
    n = models.IntegerField(default=0)
    expires = models.IntegerField()

    @classmethod
    @transaction.atomic
    def inc(cls, key, interval):
        t0 = interval * int(time() / interval)
        t1 = t0 + interval
        try:
            with transaction.atomic():
                cls.objects.create(key=key, expires=t1)
        except IntegrityError:
            pass

        counter = cls.objects.select_for_update().get(key=key)
        if counter.expires <= t0:
            counter.expires = t1
            counter.n = 0

        counter.n += 1
        counter.save()
        return counter
