from django.conf import settings


class installed:
    ratelimit = ('hoover.contrib.ratelimit' in settings.INSTALLED_APPS)
