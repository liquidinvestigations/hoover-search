from django.dispatch import receiver
from django_tus.signals import tus_upload_finished_signal
from django.conf import settings
from pathlib import Path
import shutil
import logging
import requests

log = logging.getLogger(__name__)


@receiver(tus_upload_finished_signal)
def move_file(sender, **kwargs):
    """Signal handler to move an uploaded file to it's destination path.

    Takes the filename and the collection name from the signals kwargs and
    moves the file accordingly.
    """
    orig_filename = kwargs.get('metadata').get('name')
    collection_name = kwargs.get('metadata').get('collection')
    directory_pk = int(kwargs.get('metadata').get('dirpk'))
    upload_path = Path(settings.TUS_DESTINATION_DIR, kwargs.get('filename'))
    collection_name = kwargs.get('metadata').get('collection')
    # notify snoop about the new directory and receive the full path as a string
    destination_path = Path(f'/opt/hoover/collections/{collection_name}/data'
                            + notify_snoop(collection_name, directory_pk)
                            )
    shutil.move(upload_path, get_nonexistent_filename(destination_path, orig_filename))
    log.info(f'Finished uploading file: "{orig_filename}". Moved to "{destination_path}".')


def notify_snoop(collection_name, directory_pk):
    """Calls a snoop endpoint to notify snoop that there is new file and queue a rescan of the directory.

    Returns: A string that is the full path of the directory.
    """
    url = settings.SNOOP_BASE_URL + f'/collections/{collection_name}/{directory_pk}/rescan'
    resp = requests.get(url)
    if not resp.status_code == 200:
        raise RuntimeError(f'Unexpected response: {resp}')
    else:
        return resp.content.decode()


def get_nonexistent_filename(path, filename):
    """Check if a file already exists and rename it if it does.

    If the filepath already exists: append (n) to the filename,
    until a 'n' is found for which the filepath doesn't already exist:
    e.g.: filename(3)
    """
    if not Path(path, filename).exists():
        return Path(path, filename)
    else:
        num = 1
        new_path = Path(path, f'{filename}({num})')
        while new_path.exists():
            num += 1
            new_path = Path(path, f'{filename}({num})')
        return new_path
