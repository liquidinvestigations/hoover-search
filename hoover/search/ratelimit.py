from django.conf import settings

if settings.HOOVER_RATELIMIT_USER:
    from django.http import HttpResponse
    from . import signals
    from hoover.contrib.ratelimit.limit import RateLimit

    class HttpLimitExceeded(HttpResponse):

        def __init__(self):
            super().__init__(
                "Rate limit exceeded\n", 'text/plain',
                429, 'Too Many Requests',
            )

    (_l, _i) = settings.HOOVER_RATELIMIT_USER
    _user_limit = RateLimit(_l, _i)

    def limit_user(view):
        def wrapper(request, *args, **kwargs):
            username = request.user.get_username()
            key = 'user:' + username
            if _user_limit.access(key):
                signals.rate_limit_exceeded.send(
                    'hoover.search',
                    username=username,
                )
                return HttpLimitExceeded()
            return view(request, *args, **kwargs)
        return wrapper

    def get_request_limits(user):
        if user.is_anonymous:
            return None

        key = 'user:' + user.get_username()
        return {
            'interval': _user_limit.interval,
            'limit': _user_limit.limit,
            'count': _user_limit.get(key),
        }

else:
    def limit_user(view):
        return view

    def get_request_limits(user):
        return None
