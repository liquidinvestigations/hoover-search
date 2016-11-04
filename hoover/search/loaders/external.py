from django.conf import settings
from django.http import HttpResponse, Http404
import requests
from .. import ui

class Document:

    def __init__(self, loader, root_url, doc_id):
        self.loader = loader
        self.root_url = root_url
        self.doc_id = doc_id

    def view(self, request, suffix):
        if not suffix:
            if self.loader.config.get('renderDocument'):
                url = self.root_url + self.doc_id + '/json'
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
        self.config = config

    def get(self, doc_id):
        url_root = self.config['documents']
        if not url_root.endswith('/'):
            url_root += '/'
        return Document(self, url_root, doc_id)
