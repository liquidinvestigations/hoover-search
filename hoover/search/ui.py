import logging

from django.conf import settings
from django.http import HttpResponse
import requests

log = logging.getLogger(__name__)


def proxy(request, path):
    # FIXME - urljoin cuts existing path prefix in base
    url = settings.HOOVER_UI_BASE_URL + '/' + path
    log.warning(f'proxying {path} to {url}')

    r_resp = requests.request(
        method=request.method,
        url=url,
        params=request.GET if request.method == 'GET' else {},
        data=request.body,
        headers={k: str(v) for k, v in request.META.items()},
        cookies=request.COOKIES,
    )

    c_type = r_resp.headers.get('Content-Type', 'text/html')
    d_resp = HttpResponse(
        r_resp.content,
        content_type=c_type,
        status=r_resp.status_code,
    )

    if c_type not in ['text/html']:
        d_resp['Cache-Control'] = 'max-age=31556926'

    d_resp['X-Frame-Options'] = 'SAMEORIGIN'
    return d_resp
