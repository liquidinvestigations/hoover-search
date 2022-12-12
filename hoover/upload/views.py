from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_tus.views import TusUpload
import base64
import logging

from ..search import models
from .utils import get_path
from .utils import parse_directory_id


log = logging.getLogger(__name__)


def is_uploader(collection, user):
    """Checks if a given user can upload to a collection."""
    return collection.uploader_users.filter(id=user.id).exists()


def is_collection_user(collection, user):
    """Checks if a given user can use a collection."""
    return collection.users.filter(id=user.id).exists()


def can_upload(collection_name, user):
    """Checks if a user has all permissions to upload into a collection."""
    try:
        collection = models.Collection.objects.get(name=collection_name)
    except models.Collection.DoesNotExist:
        raise Http404('collection does not exist')

    return collection.writeable and is_collection_user(collection, user) and is_uploader(collection, user)


@csrf_exempt
def upload(request, **kwargs):
    """View to upload files to a collection.

    This view checks, if the user requesting to upload has the permissions to do so for
    the given collection and if the collection allows uploading.

    The upload uses the tus protocol [[https://tus.io/protocols/resumable-upload.html]]. First a post request
    is processed to create the upload. Following that a patch request containing the uploads uuid is
    processed to do the actual uploading.

    Here the views are forwarded to the views provided by the django_tus library
    ([[https://github.com/alican/django-tus]]).

    The request is expected to include the following HTTP_UPLOAD_METADATA:
    name: <filename>, collection: <collection_name>, dirpk: <target_directory_primary_key>

    """
    if request.method == 'POST':
        metadata = parse_metadata(request.META['HTTP_UPLOAD_METADATA'])
        collection_name = metadata.get('collection')

        if not can_upload(collection_name, request.user):
            log.warning(f'User "{request.user.username}" cannot upload to collection: "{collection_name}"')
            return HttpResponseForbidden()

        log.info('Created initial upload! Metadata: ' + request.META['HTTP_UPLOAD_METADATA'])
        # forwarding request to tus view
        upload = models.Upload.objects.create(
            uploader=request.user,
            collection=models.Collection.objects.get(name=collection_name),
            directory_id=metadata.get('directory_pk'),
            filename=metadata.get('filename'),
        )
        request.META['HTTP_UPLOAD_METADATA'] = (request.META['HTTP_UPLOAD_METADATA']
                                                + ',upload_pk ' + b64_encode(str(upload.pk)))
        return (TusUpload.as_view()(request))

    if request.method == 'PATCH':
        uuid = kwargs.get('resource_id')
        log.info(f'Starting file upload! UUID: "{str(uuid)}".')
        # forward request to tus view
        return (TusUpload.as_view()(request, uuid))


def parse_metadata(metadata):
    """Parses the metadata from a metadata string and creates a dictionary.

    The string contains key value pairs, where each pair is seperated by a ',' and
    the key,value pair by a ' '. The values are base64 encoded.
    Returns a dictionary with all key,value pairs inside.
    """
    parsed_metadata = {}
    metadata = metadata.split(',')
    for entry in metadata:
        key, value = entry.split(' ')
        if key.startswith('collection'):
            parsed_metadata['collection'] = base64.b64decode(value).decode('ascii')
        elif key.startswith('name'):
            parsed_metadata['filename'] = base64.b64decode(value).decode('ascii')
        elif key.startswith('dirpk'):
            directory_str = base64.b64decode(value).decode('ascii')
            parsed_metadata['directory_pk'] = parse_directory_id(directory_str)
    return parsed_metadata


def b64_encode(s):
    """Encodes a string into a base64 encoded string."""
    s_bytes = base64.b64encode(s.encode('utf-8'))
    return s_bytes.decode('utf-8')


def get_uploads_list(request, **kwargs):
    """TODO"""
    uploads = models.Upload.objects.all()
    uploads = (uploads.filter(collection__users__in=[request.user])
               .filter(collection__uploader_users__in=[request.user]))
    print(uploads.query)
    print(uploads)
    result = [{'started': upload.started,
               'finished': upload.finished,
               'uploader': upload.uploader.username,
               'collection': upload.collection.name,
               'directory_id': upload.directory_id,
               'directory_path': upload.directory_path,
               'filename': upload.filename,
               'processed': upload.processed}
              for upload in uploads]
    return JsonResponse(result, safe=False)


def get_directory_uploads(request, collection_name, directory_id, **kwargs):
    """TODO"""

    if not can_upload(collection_name, request.user):
        log.warning(f'User "{request.user.username}" has no upload permission for: "{collection_name}"')
        return HttpResponseForbidden()

    dir_pk = parse_directory_id(directory_id)
    collection = models.Collection.objects.get(name=collection_name)
    uploads = models.Upload.objects.filter(collection=collection, directory_id=dir_pk)
    snoop_path = get_path(collection.name, dir_pk)
    result = {'directory_path': snoop_path,
              'directory_name': snoop_path.split('/')[-2],
              'collection': collection.name,
              'uploads': [{'started': upload.started,
                           'finished': upload.finished,
                           'uploader': upload.uploader.username,
                           'filename': upload.filename,
                           'processed': upload.processed,
                           'tasks_done': upload.snoop_tasks_done,
                           'tasks_total': upload.snoop_tasks_total,
                           }
                          for upload in uploads]}
    return JsonResponse(result, safe=False)
