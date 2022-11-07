"""Tasks to track user uploads into collections.

These tasks are used to keep track of the processing status of an uploaded file in hoover-snoop.
"""
from ..search import celery as cel
from django.conf import settings
from urllib.parse import quote
import time
import requests

# TODO correct queue
UPLOAD_KEY = 'hoover.search.search'


@cel.app.task(bind=True, serializer='json', name=UPLOAD_KEY, routing_key=UPLOAD_KEY, queue=UPLOAD_KEY)
def poll_processing_status(self, *args, **kwargs):
    """TODO"""
    result = file_exists(kwargs.get('collection_name'),
                         kwargs.get('directory_pk'),
                         kwargs.get('filename'),
                         )
    print('result:', result)
    return result


def file_exists(collection_name, directory_pk, filename, timeout=120):
    """Checks a snoop endpoint for the existence of a file.

    Calls the endpoint until the timeout is reached or a result is obtained.

    Args:
        collection_name: The collection name as a string.
        directory_pk: The primary key of the directory in snoop (string or int).
        filename: The original filename of the uploaded file as a string.
        timeout: The time in seconds after which the polling for a result is stopped. Defaults to 120.

    Returns:
        A tuple containing a boolean that signals if the file exists and if it does the primary key.
        Looks like: (True, pk) if file exists and (False, None) if it doesn't exist and timeout is reached.
    """
    print('filename: ')
    print(filename)
    filename_encoded = quote(filename)
    url = settings.SNOOP_BASE_URL + f'/collections/{collection_name}/{directory_pk}/{filename_encoded}/exists'
    started = time.time()
    resp = requests.get(url)
    timeout = False
    while not resp.status_code == 200 and not timeout:
        if (time.time() - started >= timeout):
            timeout = True
        # call endpoint again after 5 seconds as long as timeout is not reached
        time.sleep(5)
        resp = requests.get(url)

    file_pk = resp.content.decode()
    if timeout:
        answer = (False, None)
    else:
        answer = (True, file_pk)

    return answer
