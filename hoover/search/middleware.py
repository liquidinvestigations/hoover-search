from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin


class NoReferral(MiddlewareMixin):

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class NoCache(MiddlewareMixin):

    def process_response(self, request, response):
        if 'Cache-Control' not in response:
            add_never_cache_headers(response)
        return response
