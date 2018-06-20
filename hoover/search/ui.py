from pathlib import Path
import json
import mimetypes
from django.conf import settings
from django.http import HttpResponse, FileResponse, Http404
from django.utils.html import escapejs

NOCACHE_FILE_TYPES = ['.html']

def resolve(filename):
    ui_root = Path(settings.HOOVER_UI_ROOT)
    file = ui_root / filename
    if not (ui_root == file or ui_root in file.parents):
        raise Http404()

    if file.is_dir():
        file = file / 'index.html'

    if file.is_file():
        return file

    raise Http404()

def create_response(file):
    content_type = mimetypes.guess_type(str(file))[0] or None
    resp = FileResponse(file.open('rb'), content_type=content_type)
    if file.suffix not in NOCACHE_FILE_TYPES:
        resp['Cache-Control'] = 'max-age=31556926'
    return resp

def file(request, filename):
    return create_response(resolve(filename))

def doc_html(request, data):
    with resolve('doc/index.html').open('rt', encoding='utf-8') as f:
        html = f.read()

    data_json = escapejs(json.dumps(data))
    html = html.replace(
        '/* HOOVER HYDRATION PLACEHOLDER */',
        'window.HOOVER_HYDRATE_DOC = JSON.parse(\'{}\')'.format(data_json),
    )

    scripts = ''
    if settings.HOOVER_HYPOTHESIS_EMBED_URL:
        url = settings.HOOVER_HYPOTHESIS_EMBED_URL
        scripts += '<script src="{}"></script>'.format(url)

    html = html.replace('<!-- HOOVER SCRIPT PLACEHOLDER -->', scripts)

    return HttpResponse(html)
