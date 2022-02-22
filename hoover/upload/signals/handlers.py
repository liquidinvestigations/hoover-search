from django.dispatch import receiver
from django_tus.signals import tus_upload_finished_signal
from django.conf import settings
from pathlib import Path
import shutil
import logging


log = logging.getLogger(__name__)


@receiver(tus_upload_finished_signal)
def move_file(sender, **kwargs):
    """Signal handler to move an uploaded file to it's destination path.

    Takes the filename and the collection name from the signals kwargs and
    moves the file accordingly.
    """
    upload_path = Path(settings.TUS_DESTINATION_DIR, kwargs.get('filename'))
    collection_name = kwargs.get('metadata').get('collection')
    filename = kwargs.get('metadata').get('orig_filename')
    destination_path = Path('/opt/hoover/collections/', collection_name, 'data', filename)
    shutil.move(upload_path, destination_path)
    log.info(f'Finished uploading file: "{filename}". Moved to "{destination_path}".')
