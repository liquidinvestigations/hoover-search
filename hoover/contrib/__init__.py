from django.conf import settings

class installed:
    twofactor = ('hoover.contrib.twofactor' in settings.INSTALLED_APPS)
