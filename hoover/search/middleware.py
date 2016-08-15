from django.utils.cache import add_never_cache_headers

class NoReferral:
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        return response

class NoCache:
    def process_response(self, request, response):
        add_never_cache_headers(response)
        return response
