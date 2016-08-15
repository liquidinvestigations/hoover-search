from datetime import datetime
import urllib.request
from contextlib import contextmanager
import logging
import threading
from django.utils.timezone import UTC

LOG_LEVEL = {
    0: logging.ERROR,
    1: logging.WARN,
    2: logging.INFO,
    3: logging.DEBUG,
}


def now():
    return datetime.utcnow().replace(tzinfo=UTC())


@contextmanager
def open_url(url):
    f = urllib.request.urlopen(url)
    try:
        yield f
    finally:
        f.close()



class threadsafe(object):

    def __init__(self, iter):
        self.iter = iter
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.iter)
