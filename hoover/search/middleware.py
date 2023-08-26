import logging

from django.contrib.auth.models import User, Permission
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseNotModified

from hoover.search.models import Profile, Collection
from hoover.search.pdf_tools import split_pdf_file, get_pdf_info, pdf_extract_text
from django.utils.cache import patch_vary_headers

log = logging.getLogger(__name__)


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


class PdfHeadersMiddleware:
    """Put Vary headers for the browser to use these as part of the cache key"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.headers.get('Content-Type') == 'application/pdf':
            patch_vary_headers(response, [
                'Cookie', 'Range',
                PdfToolsMiddleware.HEADER_PDF_INFO,
                PdfToolsMiddleware.HEADER_RANGE,
                PdfToolsMiddleware.HEADER_PDF_EXTRACT_TEXT,
            ])
        return response


class PdfToolsMiddleware:
    HEADER_RANGE = 'X-Hoover-PDF-Split-Page-Range'
    HEADER_PDF_INFO = 'X-Hoover-PDF-Info'
    HEADER_PDF_EXTRACT_TEXT = 'X-Hoover-PDF-Extract-Text'
    HEADER_IGNORED = 'X-Hoover-PDF-Ignored'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # pass over unrelated requests
        get_info = request.GET.get(self.HEADER_PDF_INFO, '')
        get_range = request.GET.get(self.HEADER_RANGE, '')
        get_text = request.GET.get(self.HEADER_PDF_EXTRACT_TEXT, '')

        if (
            request.method != 'GET'
            or not (
                get_info or get_range or get_text
            )
        ):
            return self.get_response(request)

        # pop off the GET params read above
        request.GET = request.GET.copy()
        if get_info:
            del request.GET[self.HEADER_PDF_INFO]
        if get_range:
            del request.GET[self.HEADER_RANGE]
        if get_text:
            del request.GET[self.HEADER_PDF_EXTRACT_TEXT]

        # pop the request If-Modified-Since and If-None-Match
        # so the upstream service doesn't return 304 -- we will
        if request.headers.get('If-Modified-Since'):
            req_cache_date = request.headers['If-Modified-Since']
            del request.headers['If-Modified-Since']
        else:
            req_cache_date = None

        if request.headers.get('If-None-Match'):
            req_cache_etag = request.headers['If-None-Match']
            del request.headers['If-None-Match']
        else:
            req_cache_etag = None

        response = self.get_response(request)
        response['Etag'] = (
            response.headers.get('Etag', '')
            + ':' + get_info
            + ':' + get_range
            + ':' + get_text
        )
        if (
            req_cache_date and req_cache_etag
            and req_cache_date == response.headers.get('Last-Modified')
            and req_cache_etag == response.headers.get('Etag')
            and 'no-cache' not in request.headers.get('Cache-Control', '')
            and 'no-cache' not in request.headers.get('Pragma', '')
        ):
            return HttpResponseNotModified()

        # mark failure in case of unsupported operation
        if (
            request.headers.get('range')
            or response.status_code != 200
            or response.headers.get('Content-Type') != 'application/pdf'
        ):
            response = self.get_response(request)
            response[self.HEADER_IGNORED] = '1'
            return response

        assert response.streaming, 'pdf split - can only be used with streaming repsonses'
        # assert not response.is_async, 'pdf split - upstream async not supported'

        log.warning('PDF tools request STARTING... ')

        # handle PDF info
        if get_info:
            response.streaming_content = get_pdf_info(response.streaming_content)
            response['content-type'] = 'text/plain'
            response[self.HEADER_PDF_INFO] = '1'
        # handle range query
        elif get_range:
            # parse the range to make sure it's 1-100 and not some bash injection
            page_start, page_end = get_range.split('-')
            page_start, page_end = int(page_start), int(page_end)
            assert page_start > 0 and page_end > 0 and page_end > page_start, 'bad page interval'
            _range = f'{page_start}-{page_end}'

            response[self.HEADER_RANGE] = _range
            response.streaming_content = split_pdf_file(response.streaming_content, _range)

            if get_text:
                response.streaming_content = pdf_extract_text(response.streaming_content)
                response[self.HEADER_PDF_EXTRACT_TEXT] = '1'

        del response.headers['Content-Length']
        del response.headers['Content-Disposition']
        del response.headers['Accept-Ranges']
        return response
