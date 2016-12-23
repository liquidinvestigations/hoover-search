from django.http import HttpResponse, Http404
import requests
from urllib.parse import urljoin
from functools import lru_cache
from .. import ui


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

    def data_url(self, id):
        meta = self.meta()
        data_url = meta['data_urls'].replace('{id}', id)
        return urljoin(self.meta_url, data_url)

    def data(self, id):
        return get_json(self.data_url(id))

class Document:

    def __init__(self, loader, root_url, doc_id):
        self.loader = loader
        self.root_url = root_url
        self.doc_id = doc_id

    def view(self, request, suffix):
        if not suffix:
            if self.loader.config.get('renderDocument'):
                url = self.loader.api.data_url(self.doc_id)
                resp = requests.get(url)
                if 200 <= resp.status_code < 300:
                    return ui.doc_html(request, resp.json())
                elif resp.status_code == 404:
                    raise Http404
                else:
                    raise RuntimeError("Unexpected response {!r} for {!r}"
                        .format(resp, url))

        url = self.root_url + self.doc_id + suffix
        if request.GET.get('raw') == 'on':
            url += '?raw=on'
        if request.GET.get('embed') == 'on':
            url += '?embed=on'

        resp = requests.get(url)
        if 200 <= resp.status_code < 300:
            return HttpResponse(resp.content,
                content_type=resp.headers['Content-Type'])
        elif resp.status_code == 404:
            raise Http404
        else:
            raise RuntimeError("Unexpected response {!r} for {!r}"
                .format(resp, url))

class Loader:

    label = "External"

    def __init__(self, collection, **config):
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
        url_root = self.config['documents']
        if not url_root.endswith('/'):
            url_root += '/'
        return Document(self, url_root, doc_id)

    def get_metadata(self):
        return {}
