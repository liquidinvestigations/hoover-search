from django.conf import settings
import requests

class Document:

    def __init__(self, root_url, doc_id):
        self.root_url = root_url
        self.doc_id = doc_id

    def _get(self):
        return requests.get(self.root_url + self.doc_id)

    def html(self):
        resp = self._get()
        if resp.status_code == 200:
            return resp.text

        msg = "failed to get text for %s: %r" % (self.id, resp)
        raise RuntimeError(msg)

class Loader:

    label = "External"

    def __init__(self, **config):
        self.config = config

    def get_document(self, es_doc):
        return Document(self.config['documents'], es_doc['_id'])
