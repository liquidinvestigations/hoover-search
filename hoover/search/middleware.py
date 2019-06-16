from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth.middleware import RemoteUserMiddleware


class NoReferral(MiddlewareMixin):

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class NoCache(MiddlewareMixin):

    def process_response(self, request, response):
        if 'Cache-Control' not in response:
            add_never_cache_headers(response)
        return response


class AuthproxyUserMiddleware(RemoteUserMiddleware):

    header = 'HTTP_X_FORWARDED_USER'
    is_admin_header = 'HTTP_X_FORWARDED_USER_ADMIN'

    def process_request(self, request):
        if not settings.HOOVER_AUTHPROXY:
            return

        super().process_request(request)

        user = request.user
        is_admin = (request.META.get(self.is_admin_header) == 'true')
        if is_admin != user.is_superuser or is_admin != user.is_staff:
            user.is_superuser = is_admin
            user.is_staff = is_admin
            user.save()
