from . import events  # noqa
from django.core.wsgi import get_wsgi_application
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hoover.site.settings")


application = get_wsgi_application()
