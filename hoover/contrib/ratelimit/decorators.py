from django.http import HttpResponse
from django.conf import settings
from . import models
from . import signals

class HttpLimitExceeded(HttpResponse):

    def __init__(self):
        super().__init__(
            "Rate limit exceeded\n", 'text/plain',
            429, 'Too Many Requests',
        )

class RateLimit:

    def __init__(self, name, limit, interval, keyfunc):
        self.limit = limit
        self.interval = interval
        self.keyfunc = keyfunc
        self.name = name

    def access(self, key):
        n = models.Count.inc(key, self.interval)
        return n > self.limit

    def __call__(self, view):
        def wrapper(request, *args, **kwargs):
            key = self.name + ':' + self.keyfunc(request)
            if self.access(key):
                signals.rate_limit_exceeded.send(
                    models.Count,
                    request=request,
                )
                return HttpLimitExceeded()
            return view(request, *args, **kwargs)
        return wrapper

(_l, _i) = settings.HOOVER_RATELIMIT_USER
limit_user = RateLimit('user', _l, _i, lambda r: r.user.get_username())
