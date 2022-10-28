from ..search import models
from django.http import Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django_tus.views import TusUpload
import base64
import logging


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
    """

    if request.method == 'POST':
        collection_name = get_collection_name(request.META['HTTP_UPLOAD_METADATA'])

        if not can_upload(collection_name, request.user):
            log.warning(f'User "{request.user.username}" cannot upload to collection: "{collection_name}"')
            return HttpResponseForbidden()

        log.info('Created initial upload! Metadata: ' + request.META['HTTP_UPLOAD_METADATA'])
        # forwarding request to tus view
        return (TusUpload.as_view()(request))

    if request.method == 'PATCH':
        uuid = kwargs.get('resource_id')
        log.info(f'Starting file upload! UUID: "{str(uuid)}".')
        # forward request to tus view
        return(TusUpload.as_view()(request, uuid))


def get_collection_name(metadata):
    """Retrieves the collection name from a metadata string.

    The string contains key value pairs, where each pair is seperated by a ',' and
    the key,value pair by a ' '. The value is base64 encoded.
    """
    metadata = metadata.split(',')
    for entry in metadata:
        if entry.startswith('collection'):
            collection_name = entry.split(' ')[1]
            return base64.b64decode(collection_name).decode('utf-8')
