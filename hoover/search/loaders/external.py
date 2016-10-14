from django.conf import settings
from django.http import HttpResponse
import requests

class Document:

    def __init__(self, root_url, doc_id, suffix):
        self.root_url = root_url
        self.doc_id = doc_id
        self.suffix = suffix

    def _get(self):
        return requests.get(self.root_url + self.doc_id)

    def view(self, request):
        url = self.root_url + self.doc_id + self.suffix
        if request.GET.get('raw') == 'on':
            url += '?raw=on'
        if request.GET.get('embed') == 'on':
            url += '?embed=on'
        resp = requests.get(url)
        return HttpResponse(resp.content,
            content_type=resp.headers['Content-Type'])

class Loader:

    label = "External"

    def __init__(self, collection, **config):
        self.config = config

    def get(self, doc_id, suffix):
        url_root = self.config['documents']
        if not url_root.endswith('/'):
            url_root += '/'
        return Document(url_root, doc_id, suffix)
