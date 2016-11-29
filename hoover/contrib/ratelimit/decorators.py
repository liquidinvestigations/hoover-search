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

    def __init__(self, limit, interval):
        self.limit = limit
        self.interval = interval

    def access(self, key):
        n = models.Count.inc(key, self.interval)
        return n > self.limit

(_l, _i) = settings.HOOVER_RATELIMIT_USER
_user_limit = RateLimit(_l, _i)

def limit_user(view):
    def wrapper(request, *args, **kwargs):
        key = 'user:' + request.user.get_username()
        if _user_limit.access(key):
            signals.rate_limit_exceeded.send(
                models.Count,
                request=request,
            )
            return HttpLimitExceeded()
        return view(request, *args, **kwargs)
    return wrapper
