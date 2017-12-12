from . import models

class RateLimit:

    def __init__(self, limit, interval):
        self.limit = limit
        self.interval = interval

    def access(self, key):
        n = models.Count.inc(key, self.interval)
        return n > self.limit

    def get(self, key):
        return models.Count.get(key, self.interval)
