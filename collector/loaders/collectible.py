import re
import json
import logging
from tempfile import TemporaryFile
from django.conf import settings
from django.http import HttpResponse
import yaml
import requests
from ..utils import open_url
from .. import tika

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Url(object):

    def __init__(self, url):
        self.url = url

    def __str__(self):
        return self.url

    def open(self):
        return open_url(self.url)

    def join(self, value):
        if re.match(r'^http[s]?://', value):
            return Url(value)

        else:
            return Url(self.url.rsplit('/', 1)[0] + '/' + value)


class Document(object):

    def __init__(self, metadata):
        self.metadata = metadata

    def text(self):
        resp = requests.get(self.metadata['text_url'])

        if resp.status_code == 200:
            return resp.text

        msg = "failed to get text %s: %r" % (self.metadata['id'], resp)
        raise RuntimeError(msg)

    def _open(self):
        tmp = TemporaryFile()
        resp = requests.get(self.metadata['url'], stream=True)
        for chunk in resp.iter_content(256*1024):
            tmp.write(chunk)
        tmp.seek(0)
        return tmp

    def view(self, request):
        if request.GET.get('raw') == 'on':
            with self._open() as tmp:
                return HttpResponse(tmp.read(),
                    content_type='application/octet-stream')

        else:
            with self._open() as tmp:
                html = tika.html(tmp)
            if settings.EMBED_HYPOTHESIS:
                html += '\n' + settings.EMBED_HYPOTHESIS
            return HttpResponse(html)


class Loader(object):

    label = "Collectible"

    def __init__(self, collection, index, match='', **config):
        self.collection = collection
        self.index = Url(index)
        self.match = match

    def get_metadata(self):
        logger.info("loading collection %s", self.index)
        with self.index.open() as i:
            return yaml.safe_load(i)

    def documents(self):
        for doc in self.get_metadata()['documents']:
            doc_url = self.index.join(doc)
            logger.info("loading document list %s", doc_url)
            with doc_url.open() as d:
                for line in d:
                    metadata = json.loads(line.decode('utf-8'))
                    metadata['url'] = doc_url.join(data['url']).url
                    metadata['text_url'] = doc_url.join(data['text_url']).url
                    yield Document(metadata)

    def get(self, doc_id):
        es_doc = self.collection.get_document(doc_id)
        return Document(es_doc['_source'])
