import time
import logging
from urllib.parse import urljoin

from django.http import Http404, StreamingHttpResponse
from django.conf import settings
import requests

log = logging.getLogger(__name__)


def get_json(url, retries=5, retry_delay_sec=.5):
    """Gets JSON content using requests.get. Tries a few times to get a 200 OK response."""

    for i in range(retries):
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
        log.warning(f'HTTP {resp.status_code} for {url} (retrying {i+1}/{retries})')
        time.sleep(retry_delay_sec)
    raise RuntimeError(f"Unexpected HTTP {resp.status_code} response from {url}! Content: {resp.content[:2000]}")


class Api:

    def __init__(self, meta_url):
        self.meta_url = meta_url
        self.meta = get_json(self.meta_url)

    def feed(self, url):
        if url is None:
            url = urljoin(self.meta_url, self.meta['feed'])

        resp = get_json(url)
        next_url = resp.get('next')
        if next_url:
            next_url = urljoin(url, next_url)
        return (resp['documents'], next_url)

    def data_url(self, id):
        data_url = self.meta['data_urls'].replace('{id}', id)
        return urljoin(self.meta_url, data_url)

    def data(self, id):
        return get_json(self.data_url(id))


class Document:
    RETRY_COUNT = 5
    RETRY_INTERVAL_SEC = 1.0

    def __init__(self, loader, doc_id):
        self.loader = loader
        self.doc_id = doc_id

    def view(self, request, suffix):
        for retry in range(1, self.RETRY_COUNT + 1):
            try:
                return self._view(request, suffix)
            except Exception as e:
                log.warning('upstream view failed, retry %s/%s: %s', retry, self.RETRY_COUNT, str(type(e)))
                if retry >= self.RETRY_COUNT:
                    raise e
                else:
                    time.sleep(self.RETRY_INTERVAL_SEC * retry)

    def _view(self, request, suffix):
        url = self.loader.api.data_url(self.doc_id)
        CHUNK_SIZE = 2**16  # 64k

        if not suffix:
            raise Http404

        url_with_suffix = urljoin(url, suffix[1:])
        headers = {
            h: request.headers[h]
            for h in settings.SNOOP_REQUEST_FORWARD_HEADERS
            if h in request.headers
        }
        data_resp = requests.get(
            url_with_suffix,
            params=request.GET,
            headers=headers,
            stream=True,
        )
        if 200 <= data_resp.status_code < 400:
            resp = StreamingHttpResponse(
                data_resp.iter_content(chunk_size=CHUNK_SIZE),
                status=data_resp.status_code,
            )
            for k, v in data_resp.headers.items():
                if k in settings.SNOOP_RESPONSE_FORWARD_HEADERS:
                    resp[k] = v
            return resp
        elif data_resp.status_code == 404:
            raise Http404
        else:
            raise RuntimeError(
                "Unexpected response {!r} for {!r}".format(data_resp, url_with_suffix))


class Loader:

    label = "External"

    def __init__(self, **config):
        self.api = Api(config['url'])
        self.config = config

    def feed_page(self, url):
        (documents, next_url) = self.api.feed(url)
        documents_with_data = [
            doc if 'content' in doc else self.api.data(doc['id'])
            for doc in documents
        ]
        return (documents_with_data, next_url)

    def get(self, doc_id):
        return Document(self, doc_id)

    def get_metadata(self):
        return {}
