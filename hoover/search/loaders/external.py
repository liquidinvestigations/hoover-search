from django.conf import settings
from django.http import HttpResponse, Http404
import requests
from .. import ui

class Document:

    def __init__(self, loader, root_url, doc_id, suffix):
        self.loader = loader
        self.root_url = root_url
        self.doc_id = doc_id
        self.suffix = suffix

    def _get(self):
        return requests.get(self.root_url + self.doc_id)

    def view(self, request):
        if not self.suffix:
            if self.loader.config.get('renderDocument'):
                return ui.doc_html(request)

        url = self.root_url + self.doc_id + self.suffix
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
            raise RuntimeError

class Loader:

    label = "External"

    def __init__(self, collection, **config):
        self.config = config

    def get(self, doc_id, suffix):
        url_root = self.config['documents']
        if not url_root.endswith('/'):
            url_root += '/'
        return Document(self, url_root, doc_id, suffix)
