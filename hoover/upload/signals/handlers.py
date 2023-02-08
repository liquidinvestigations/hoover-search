from django.dispatch import receiver
from django_tus.signals import tus_upload_finished_signal
from django.conf import settings
from django.utils import timezone
from pathlib import Path
from ..tasks import poll_processing_status
from ..views import parse_directory_id
import shutil
import logging
import requests
import uuid

from hoover.search import models
from ..utils import get_path

log = logging.getLogger(__name__)


@receiver(tus_upload_finished_signal)
def move_file(sender, **kwargs):
    """Signal handler to move an uploaded file to it's destination path.

    Takes the filename and the collection name from the signals kwargs and
    moves the file accordingly.
    """
    orig_filename = kwargs.get('metadata').get('name')
    collection_name = kwargs.get('metadata').get('collection')
    directory_pk_raw = kwargs.get('metadata').get('dirpk')
    directory_pk = int(parse_directory_id(directory_pk_raw))
    upload_pk = int(kwargs.get('metadata').get('upload_pk'))
    upload_path = Path(settings.TUS_DESTINATION_DIR, kwargs.get('filename'))
    collection_name = kwargs.get('metadata').get('collection')
    # create uuid from uuid string which is the last part of the upload path
    upload_uuid = uuid.UUID(Path(kwargs.get('upload_file_path')).name)

    snoop_path = get_path(collection_name, directory_pk)

    upload = models.Upload.objects.get(pk=upload_pk)
    upload.upload_id = upload_uuid
    upload.finished = timezone.now()
    upload.directory_path = snoop_path
    upload.save()
    # notify snoop about the new directory and receive the full path as a string
    destination_path = settings.SNOOP_COLLECTION_DIR / collection_name / f'data{snoop_path}'
    nonexistent_destination_path, snoop_filename = get_nonexistent_filename(destination_path, orig_filename)
    shutil.move(upload_path, nonexistent_destination_path)
    notify_snoop(collection_name, directory_pk)
    poll_kwargs = {'filename': snoop_filename,
                   'directory_pk': directory_pk,
                   'collection_name': collection_name,
                   'upload_pk': upload.pk}
    async_result = poll_processing_status.apply_async(
        kwargs=poll_kwargs,
    )
    upload.poll_task = async_result.id
    upload.save()

    log.info(f'Finished uploading file: "{orig_filename}". Moved to "{destination_path}".')
    log.info('Started task to monitor processing status.')


def notify_snoop(collection_name, directory_pk):
    """Calls a snoop endpoint to notify snoop that there is new file and queue a rescan of the directory.
    """
    url = settings.SNOOP_BASE_URL + f'/collections/{collection_name}/{directory_pk}/rescan'
    resp = requests.get(url)
    if not resp.status_code == 200:
        raise RuntimeError(f'Unexpected response: {resp}')


def get_nonexistent_filename(path, filename):
    """Check if a file already exists and rename it if it does.

    If the filepath already exists: append (n) to the filename,
    until a 'n' is found for which the filepath doesn't already exist:
    e.g.: filename(3).

    Args:
        path: A pathlike object or string.
        filename: Filename as a string.

    Returns:
        A tuple with the unique full path of the file and the resulting filename: (full_path, filename)
    """
    if not Path(path, filename).exists():
        return (Path(path, filename), filename)
    else:
        num = 1
        new_filename = f'{filename}({num})'
        new_path = Path(path, new_filename)
        while new_path.exists():
            num += 1
            new_filename = f'{filename}({num})'
            new_path = Path(path, new_filename)
        return (new_path, new_filename)
