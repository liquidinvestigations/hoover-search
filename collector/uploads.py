import os
import re
import zipfile
from django.conf import settings
from . import index


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
    collection_path = uploads_root + collection.slug + '/'
    for local_path in save_zipfile(collection_path, uploaded_file):
        if os.path.isdir(local_path):
            continue

        print [local_path, uploads_root]
        assert local_path.startswith(collection_path)
        relative_path = local_path[len(uploads_root):]
        local_url = settings.HOOVER_UPLOADS_URL + relative_path
        url = request.build_absolute_uri(local_url)

        try:
            index.index_local_file(collection, local_path, relative_path, url)

        except Exception as e:
            yield ('fail', relative_path, str(e))

        else:
            yield ('success', relative_path)
