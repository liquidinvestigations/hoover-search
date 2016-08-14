from pathlib import Path
import subprocess
from django.conf import settings
from django.http import HttpResponse
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

    def _open(self):
        return self.local_path.open('rb')

    def view(self, request):
        if self.local_path.suffix == '.pdf':
            mime_type = 'application/pdf'
        else:
            mime_type = 'application/octet-stream'

        if request.GET.get('raw') == 'on':
            with self._open() as tmp:
                return HttpResponse(tmp.read(), content_type=mime_type)

        else:
            if settings.HOOVER_PDFJS_URL and mime_type == 'application/pdf':
                raw = request.build_absolute_uri() + '?raw=on'
                url = settings.HOOVER_PDFJS_URL + 'viewer.html?file=' + quote(raw)
                return HttpResponseRedirect(url)

            else:
                with self._open() as tmp:
                    html = tika.html(tmp)
                if settings.EMBED_HYPOTHESIS:
                    html += '\n' + settings.EMBED_HYPOTHESIS
                return HttpResponse(html)


def walk(folder):
    for item in folder.iterdir():
        if item.is_dir():
            yield from walk(item)
            continue
        yield item


class Loader:

    label = "Upload"

    def __init__(self, collection, **config):
        self.config = config

    def get_metadata(self):
        return self.config

    def documents(self):
        for item in walk(UPLOADS_ROOT / self.config['name']):
            if item.suffix == '.pdf':
                yield Document(item)

    def get(self, doc_id):
        return Document(UPLOADS_ROOT / doc_id)
