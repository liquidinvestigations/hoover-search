"""
Loader for https://github.com/hoover/search/wiki/Collections-API
"""

from urllib.parse import urljoin
from functools import lru_cache
import re
from django.http import JsonResponse
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

    def feed(self, url):
        if url is None:
            url = urljoin(self.meta_url, self.meta()['feed'])

        resp = get_json(url)
        next_url = resp.get('next')
        if next_url:
            next_url = urljoin(url, next_url)
        return (resp['documents'], next_url)

    def data(self, id):
        meta = self.meta()
        data_url = meta['data_urls'].replace('{id}', id)
        return get_json(urljoin(self.meta_url, data_url))

class Document:

    def __init__(self, loader, id):
        self.loader = loader
        self.id = id

    def view(self, request, suffix):
        return JsonResponse(self.get_data())

    def get_data(self):
        return self.loader.api.data(self.id)

class Loader:

    label = "Json API"

    def __init__(self, collection, **config):
        self.api = Api(config['url'])

    def get_metadata(self):
        return {}

    def feed_page(self, url):
        (documents, next_url) = self.api.feed(url)
        documents_with_data = [
            doc if 'content' in doc else self.api.data(doc['id'])
            for doc in documents
        ]
        return (documents_with_data, next_url)

    def get(self, doc_id):
        return Document(self, doc_id)
