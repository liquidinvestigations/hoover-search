import logging
from urllib.parse import urlparse, unquote
from tempfile import TemporaryFile
from django.conf import settings
from django.http import HttpResponse
import easywebdav
from .. import tika

from easywebdav import client as _easywebdav_client
if not hasattr(_easywebdav_client, 'basestring'):
    _easywebdav_client.basestring = str

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Document(object):

    def __init__(self, dav, filename, mime_type):
        self.dav = dav
        self.filename = filename
        self.mime_type = mime_type

    @property
    def metadata(self):
        rv = {
            'id': self.filename,
            'title': unquote(self.filename),
            'mime_type': self.mime_type,
        }
        return rv

    def _open(self):
        tmp = TemporaryFile()
        self.dav.download(self.filename, tmp)
        tmp.seek(0)
        return tmp

    def text(self):
        with self._open() as tmp:
            return tika.text(tmp)

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

    label = "WebDAV"

    def __init__(self, collection, **config):
        self.collection = collection
        self.config = config
        self.source_url = urlparse(self.config['source'])
        self.base_path = '/' + self.source_url.path.strip('/') + '/'

    def get_metadata(self):
        return self.config

    def _dav(self):
        return easywebdav.connect(
            protocol=self.source_url.scheme,
            host=self.source_url.hostname,
            username=self.source_url.username,
            password=self.source_url.password,
            path=self.base_path.strip('/'),
        )

    def documents(self):
        dav = self._dav()

        def _files(parent):
            logger.debug('listing %r', parent)
            for f in dav.ls(parent):
                assert f.name.startswith(self.base_path)
                filename = f.name[len(self.base_path):]
                if filename == parent: continue
                if filename.endswith('/'):
                    yield from _files(filename)
                else:
                    yield (filename, f)

        for filename, file_obj in _files(''):
            mime_type = file_obj.contenttype.split(';')[0]
            yield Document(dav, filename, mime_type)

    def get(self, doc_id, suffix):
        es_doc = self.collection.get_document(doc_id)
        dav = self._dav()
        return Document(dav, doc_id, es_doc['_source']['mime_type'])
