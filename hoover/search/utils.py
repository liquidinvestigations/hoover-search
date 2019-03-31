from datetime import datetime
import urllib.request
from contextlib import contextmanager
import logging
from django.utils.timezone import utc

LOG_LEVEL = {
    0: logging.ERROR,
    1: logging.WARN,
    2: logging.INFO,
    3: logging.DEBUG,
}


def now():
    return datetime.utcnow().replace(tzinfo=utc())


@contextmanager
def open_url(url):
    f = urllib.request.urlopen(url)
    try:
        yield f
    finally:
        f.close()


class Middleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request) or self.get_response(request)
        return self.process_response(request, response)

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        return response
