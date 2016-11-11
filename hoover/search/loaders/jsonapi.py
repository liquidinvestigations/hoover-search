"""
Loader for https://github.com/hoover/search/wiki/Collections-API
"""

from urllib.parse import urljoin
from functools import lru_cache
import re
from django.http import HttpResponse, Http404
import requests
from .. import ui, models

@lru_cache(maxsize=32)
def get_json(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError("Unexpected response from {}: {!r}"
            .format(url, resp))
    return resp.json()

class Api:

    def __init__(self, meta_url):
        self.meta_url = meta_url

    def meta(self):
        return get_json(self.meta_url)

    def feed(self):
        url = urljoin(self.meta_url, self.meta()['feed'])
        while True:
            resp = get_json(url)
            yield from resp['documents']

            next_url = resp.get('next')
            if not next_url:
                break
            url = urljoin(url, next_url)

    def data(self, id):
        meta = self.meta()
        m = re.match(meta['id_pattern'], id)
        id_parts = dict(m.groupdict(), id=id)
        data_url = meta['data_urls'].format(**id_parts)
        return get_json(urljoin(self.meta_url, data_url))

class Document:

    def __init__(self, loader, id):
        self.loader = loader
        self.id = id

    def view(self, request, suffix):
        raise NotImplementedError

    @property
    def metadata(self):
        return self.loader.api.data(self.id)

    def text(self):
        return self.metadata.get('text')

class Loader:

    label = "Json API"

    def __init__(self, collection, **config):
        self.api = Api(config['url'])

    def documents(self):
        for item in self.api.feed():
            yield Document(self, item['id'])

    def get(self, doc_id):
        return Document(self, doc_id)
