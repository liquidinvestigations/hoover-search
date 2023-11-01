from . import celery as cel
# from datetime import datetime
# from django.conf import settings
# import logging
from webdav3.client import Client
from django.contrib.auth import get_user_model
# from . import models


SYNC_KEY = 'hoover.search.nexctloudsync'

# TODO
WEBDAV_ROOT = 'path'


@cel.app.task(bind=True, queue=SYNC_KEY, name=SYNC_KEY, max_retries=None)
def sync_nextcloud_directories():
    users = get_user_model().objects.all()
    for user in users:
        options = {
            'webdav_hostname': WEBDAV_ROOT + '/user',
            'webdav_login': user.name,
            'webdav_password': '4BdLzU9tOWul5xmMGg1D',
        }
        client = Client(options)
        directories = recurse_nextcloud_directories('/', 4, client)
        for directory in directories:
            # models.NextcloudDirectory.create(
            #     name=directory['name'],
            #     path=directory['path'],
            #     modified=datetime.strptime(directory['modified'],
            #                                '%a, %d %b %Y %H:%M:%S %Z')
            # )
            pass


def recurse_nextcloud_directories(path, max_depth, client, max_size=20, depth=0):
    content = client.list(path, get_info=True)
    directories = [x for x in content if x['isdir']]
    dir_list = []
    dir_list.extend(directories)

    if depth == max_depth:
        return []
    if len(dir_list) > max_size:
        dir_list = dir_list[:10]
        return dir_list

    for directory in directories:
        # check if a directory with this path exists in the database
        # and if it was currently modified
        # if it wasn't modified we don't recurse it
        # if models.NextcloudDirectory.objects.filter(path=directory['path']).exists():
        #     modified = datetime.strptime(directory['modified'], '%a, %d %b %Y %H:%M:%S %Z')
        #     directory_in_db = models.NextcloudDirectory.objects.get(path=directory['path'])
        #     if modified == directory_in_db.modified:
        #         continue
        # else:
        new_content = recurse_nextcloud_directories(directory['path'],
                                                    max_depth,
                                                    depth=depth + 1)
        if new_content:
            new_directories = [x for x in new_content if x['isdir']]
            if len(new_directories) + len(dir_list) > max_size:
                remaining = max_size - len(dir_list)
                new_directories = new_directories[:remaining]
                dir_list += new_directories
    return dir_list
