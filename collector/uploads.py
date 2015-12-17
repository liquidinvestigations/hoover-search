import re
import zipfile
from django.conf import settings


def save_zipfile(collection, uploaded_file):
    uploads_root = settings.HOOVER_UPLOADS_ROOT + '/'
    out_dir = uploads_root + collection.slug + '/'
    zf = zipfile.ZipFile(uploaded_file)
    for item in zf.infolist():
        name = item.filename
        if re.search(r'^[_\.]', name) or re.search(r'/[_\.]', name):
            continue
        out_path = zf.extract(item, out_dir)
        assert out_path.startswith(out_dir)
        local_url = settings.HOOVER_UPLOADS_URL + out_path[len(uploads_root):]
        yield local_url


def handle_zipfile(request, collection, uploaded_file):
    for local_url in save_zipfile(collection, uploaded_file):
        print request.build_absolute_uri(local_url)
