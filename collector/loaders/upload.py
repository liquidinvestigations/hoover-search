from pathlib import Path
import subprocess
from django.conf import settings
from .. import tika

UPLOADS_ROOT = Path(settings.HOOVER_UPLOADS_ROOT)


class Document:

    def __init__(self, local_path):
        relative_path = str(local_path.relative_to(UPLOADS_ROOT))
        self.local_path = local_path
        self.id = relative_path
        self.url = (
            settings.HOOVER_BASE_URL +
            settings.HOOVER_UPLOADS_URL +
            relative_path
        )

    @property
    def metadata(self):
        rv = {
            'id': self.id,
            'title': self.id,
            'url': self.url,
        }
        if self.local_path.suffix == '.pdf':
            rv['mime_type'] = 'application/pdf'
        return rv

    def text(self):
        args = ['pdftotext', str(self.local_path), '-']
        return subprocess.check_output(args).decode('utf-8')

    def open(self):
        return self.local_path.open('rb')

    def html(self):
        with self.open() as tmp:
            return tika.html(tmp)


def walk(folder):
    for item in folder.iterdir():
        if item.is_dir():
            yield from walk(item)
            continue
        yield item


class Loader:

    label = "Upload"

    def __init__(self, **config):
        self.config = config

    def get_metadata(self):
        return self.config

    def documents(self):
        for item in walk(UPLOADS_ROOT / self.config['name']):
            if item.suffix == '.pdf':
                yield Document(item)

    def get_document(self, es_doc):
        return Document(UPLOADS_ROOT / es_doc['_id'])
