import os
import re
import zipfile
import mimetypes
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from . import index
from .loaders.upload import Document

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
    collection_path = UPLOADS_ROOT / collection.name
    zip_files = save_zipfile(str(collection_path), uploaded_file)
    for local_path in (Path(p) for p in zip_files):
        if local_path.is_dir():
            continue

        assert collection_path in local_path.parents
        relative_path = local_path.relative_to(UPLOADS_ROOT)

        if local_path.suffix != '.pdf':
            yield ('fail', relative_path, "unknown file type")
            continue

        index.index(collection, Document(local_path))
        yield ('success', relative_path)


def serve_file(request, filename):
    file_path = UPLOADS_ROOT / filename
    if not (UPLOADS_ROOT in file_path.parents and file_path.is_file()):
        raise Http404()
    content_type = (mimetypes.guess_type(str(file_path))[0]
        or 'application/octet-stream')
    resp = FileResponse(
        file_path.open('rb'),
        content_type=content_type,
    )
    resp['Access-Control-Allow-Origin'] = settings.HOOVER_PDFJS_URL
    return resp
