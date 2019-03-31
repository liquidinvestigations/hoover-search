from django.utils.cache import add_never_cache_headers
from .utils import Middleware


class NoReferral(Middleware):

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class NoCache(Middleware):

    def process_response(self, request, response):
        if 'Cache-Control' not in response:
            add_never_cache_headers(response)
        return response
