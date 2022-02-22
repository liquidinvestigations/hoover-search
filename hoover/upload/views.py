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
def upload(request, collection_name, **kwargs):
    """View to upload files to a collection.

    This view checks, if the user requesting to upload has the permissions to do so for
    the given collection and if the collection allows uploading.

    The upload uses the tus protocol [[https://tus.io/protocols/resumable-upload.html]]. First a post request
    is processed to create the upload. Following that a patch request containing the uploads uuid is
    processed to do the actual uploading.

    Here the views are forwarded to the views provided by the django_tus library
    ([[https://github.com/alican/django-tus]]).
    """
    if not can_upload(collection_name, request.user):
        log.warning(f'User "{request.user.username}" cannot upload to collection: "{collection_name}"')
        return HttpResponseForbidden()

    if request.method == 'POST':
        upload_meta = request.META.get('HTTP_UPLOAD_METADATA')
        collection_bytes = base64.b64encode(collection_name.encode('utf-8'))
        collection_b64_str = collection_bytes.decode('utf-8')
        request.META['HTTP_UPLOAD_METADATA'] = upload_meta + ',collection ' + collection_b64_str
        log.info('Created initial upload! Metadata: ' + upload_meta)
        return(TusUpload.as_view()(request))

    if request.method == 'PATCH':
        uuid = kwargs.get('resource_id')
        log.info(f'Starting file upload! UUID: "{str(uuid)}".')
        return(TusUpload.as_view()(request, uuid))
