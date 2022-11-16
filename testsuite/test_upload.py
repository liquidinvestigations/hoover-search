import pytest
import base64
import re
import os
import filecmp
import responses
from django.urls import reverse
from django.conf import settings
from hoover.search import models

pytestmark = pytest.mark.django_db
TESTFILE_PATH = '/opt/hoover/collections/testdata/data/original.pdf'


def encode_str(input_str):
    string_bytes = base64.b64encode(input_str.encode('utf-8'))
    return string_bytes.decode('utf-8')


def setup_collection(django_user_model):
    user = django_user_model.objects.create_user(username='testuser', password='pw')
    col = models.Collection.objects.create(
        name='testdata',
        index='hoover-testdata',
        public=True,
        writeable=True,
    )
    col.users.add(user)
    col.uploader_users.add(user)
    return col


@responses.activate
def test_search_upload(client, django_user_model):
    setup_collection(django_user_model)
    user = django_user_model.objects.get(username='testuser')
    url = reverse('tus_upload')

    responses.add(responses.GET,
                  settings.SNOOP_BASE_URL + '/collections/testdata/1/path',
                  body='/',
                  status=200,
                  )

    responses.add(responses.GET,
                  settings.SNOOP_BASE_URL + '/collections/testdata/1/rescan',
                  status=200,
                  )

    # for details see https://tus.io/protocols/resumable-upload.html#post
    post_headers = {
        'HTTP_UPLOAD_METADATA': ('name ' + encode_str('test.pdf')
                                 + ',collection ' + encode_str('testdata')
                                 + ',dirpk ' + encode_str('1')),
        'HTTP_CONTENT_LENGTH': '0',
        'HTTP_UPLOAD_LENGTH': '2681358',  # file size in bytes
        'HTTP_TUS_RESUMABLE': '1.0.0'
    }

    # for details see https://tus.io/protocols/resumable-upload.html#patch
    patch_headers = {
        'HTTP_UPLOAD_OFFSET': '0',
        'HTTP_CONTENT_LENGTH': '2681358',  # file size in bytes
        'HTTP_CONTENT_TYPE': 'application/offset+octet-stream',
        'HTTP_TUS_RESUMABLE': '1.0.0'
    }
    client.force_login(user)
    initial_response = client.post(url, **post_headers)
    assert initial_response.status_code == 201

    upload_location = initial_response.get('Location')
    upload_url = re.search('/api/.+', upload_location).group(0)

    with open(TESTFILE_PATH, 'rb') as f:
        data = f.read()

    upload_response = client.patch(upload_url, data=data, **patch_headers)
    assert upload_response.status_code == 204

    assert os.path.isfile('/opt/hoover/collections/testdata/data/test.pdf')
    assert filecmp.cmp('/opt/hoover/collections/testdata/data/test.pdf', TESTFILE_PATH, shallow=True)
    os.remove('/opt/hoover/collections/testdata/data/test.pdf')
