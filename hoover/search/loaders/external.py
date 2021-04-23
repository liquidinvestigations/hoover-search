from django.http import HttpResponse, Http404
import requests
from urllib.parse import urljoin


def get_json(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError("Unexpected response from {}: {!r}"
                           .format(url, resp))
    return resp.json()


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

    def __init__(self, loader, doc_id):
        self.loader = loader
        self.doc_id = doc_id

    def view(self, request, suffix):
        url = self.loader.api.data_url(self.doc_id)

        if not suffix:
            raise Http404

        # fake filename, prevents url encoding errors
        # if suffix.startswith('/raw/'):
        #     suffix = '/raw/data'

        url_with_suffix = urljoin(url, suffix[1:])
        data_resp = requests.get(url_with_suffix, params=request.GET)
        if 200 <= data_resp.status_code < 300:
            resp = HttpResponse(data_resp.content,
                                content_type=data_resp.headers['Content-Type'])
            for k, v in data_resp.headers.items():
                if k in ['Content-Disposition']:
                    resp[k] = v
            return resp
        elif data_resp.status_code == 404:
            raise Http404
        else:
            raise RuntimeError("Unexpected response {!r} for {!r}"
                               .format(data_resp, url_with_suffix))


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
