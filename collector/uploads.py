import os
import re
import zipfile
import mimetypes
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from . import index

UPLOADS_ROOT = Path(settings.HOOVER_UPLOADS_ROOT)


def save_zipfile(out_dir, uploaded_file):
    zf = zipfile.ZipFile(uploaded_file)
    for item in zf.infolist():
        name = item.filename
        if re.search(r'^[_\.]', name) or re.search(r'/[_\.]', name):
            continue
        local_path = zf.extract(item, out_dir)
        yield local_path


def handle_zipfile(request, collection, uploaded_file):
    uploads_root = settings.HOOVER_UPLOADS_ROOT + '/'
    collection_path = uploads_root + collection.name + '/'
    for local_path in save_zipfile(collection_path, uploaded_file):
        if os.path.isdir(local_path):
            continue

        assert local_path.startswith(collection_path)
        relative_path = local_path[len(uploads_root):]
        local_url = settings.HOOVER_UPLOADS_URL + relative_path

        if not local_path.endswith('.pdf'):
            yield ('fail', relative_path, "unknown file type")
            continue

        url = request.build_absolute_uri(local_url)
        index.index_local_file(collection, local_path, relative_path, url)
        yield ('success', relative_path)


def serve_file(request, filename):
    file_path = UPLOADS_ROOT / filename
    print(file_path)
    if not (UPLOADS_ROOT in file_path.parents and file_path.is_file()):
        raise Http404()
    content_type = (mimetypes.guess_type(str(file_path))[0]
        or 'application/octet-stream')
    return FileResponse(file_path.open('rb'), content_type=content_type)
