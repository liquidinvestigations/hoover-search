from django.conf import settings
import requests


def parse_directory_id(raw_id):
    return raw_id.split('_')[-1]


def get_path(collection_name, directory_pk):
    """Calls a snoop endpoint to notify snoop that there is new file and queue a rescan of the directory.

    Returns: A string that is the full path of the directory.
    """
    url = settings.SNOOP_BASE_URL + f'/collections/{collection_name}/{directory_pk}/path'
    resp = requests.get(url)
    if not resp.status_code == 200:
        raise RuntimeError(f'Unexpected response: {resp}')
    else:
        return resp.content.decode()
