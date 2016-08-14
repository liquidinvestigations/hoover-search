import logging
from urllib.parse import urlparse, unquote
from tempfile import TemporaryFile
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

    def open(self):
        tmp = TemporaryFile()
        self.dav.download(self.filename, tmp)
        tmp.seek(0)
        return tmp

    def text(self):
        with self.open() as tmp:
            return tika.text(tmp)

    def html(self):
        with self.open() as tmp:
            return tika.html(tmp)


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

    def get_document(self, es_doc):
        id = es_doc['_id']
        mime_type = es_doc['_source']['mime_type']
        dav = self._dav()
        return Document(dav, id, mime_type)
