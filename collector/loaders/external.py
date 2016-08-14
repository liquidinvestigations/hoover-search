from django.conf import settings
from django.http import HttpResponse
import requests

class Document:

    def __init__(self, root_url, doc_id):
        self.root_url = root_url
        self.doc_id = doc_id

    def _get(self):
        return requests.get(self.root_url + self.doc_id)

    def view(self, request):
        url = self.root_url + self.doc_id
        if request.GET.get('raw') == 'on':
            url += '?raw=on'
        resp = requests.get(url)
        return HttpResponse(resp.content,
            content_type=resp.headers['Content-Type'])

class Loader:

    label = "External"

    def __init__(self, collection, **config):
        self.config = config

    def get(self, doc_id):
        return Document(self.config['documents'], doc_id)
