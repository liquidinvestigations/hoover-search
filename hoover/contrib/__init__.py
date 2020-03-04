from django.conf import settings


class installed:
    twofactor = ('hoover.contrib.twofactor' in settings.INSTALLED_APPS)
    oauth2 = ('hoover.contrib.oauth2' in settings.INSTALLED_APPS)
    ratelimit = ('hoover.contrib.ratelimit' in settings.INSTALLED_APPS)
