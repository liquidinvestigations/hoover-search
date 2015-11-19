from datetime import datetime
import urllib
from contextlib import contextmanager
from django.utils.timezone import UTC


def now():
    return datetime.utcnow().replace(tzinfo=UTC())


@contextmanager
def open_url(url):
    f = urllib.urlopen(url)
    try:
        yield f
    finally:
        f.close()
