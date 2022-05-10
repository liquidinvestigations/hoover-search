from django.contrib.auth.models import User, Permission
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.contenttypes.models import ContentType

from hoover.search.models import Profile, Collection


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

    def process_request(self, request):
        if not settings.HOOVER_AUTHPROXY:
            return

        super().process_request(request)

        if not request.META.get(self.header):
            return

        user = request.user
        username = request.META.get(self.header)
        assert user.username == username

        email = request.META.get('HTTP_X_FORWARDED_EMAIL')
        full_name = request.META.get('HTTP_X_FORWARDED_PREFERRED_USERNAME')
        groups = [
            x.strip()
            for x in request.META.get('HTTP_X_FORWARDED_GROUPS').split(',')
        ]

        is_admin = ('admin' in groups)
        is_superuser = ('superuser' in groups)
        save = False
        if not User.objects.filter(username=username).exists():
            save = True

        if is_superuser != user.is_superuser or is_admin != user.is_staff:
            user.is_superuser = is_superuser
            user.is_staff = is_admin
            save = True

        if is_admin:
            collection_type = ContentType.objects.get_for_model(Collection)
            collection_permissions = Permission.objects.filter(content_type=collection_type)
            for perm in collection_permissions:
                user.user_permissions.add(perm)

        if email != user.email:
            user.email = email
            save = True

        if full_name != user.get_full_name() and \
                full_name != user.get_username() and \
                ' ' in full_name:
            user.first_name, user.last_name = full_name.split(' ', maxsplit=1)
            save = True

        if save:
            user.set_unusable_password()
            user.save()
            Profile.objects.get_or_create(user=user)
