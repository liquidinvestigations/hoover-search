from datetime import datetime
from django.conf import settings
import logging
from webdav3.client import Client
from django.contrib.auth import get_user_model
from . import models

log = logging.getLogger(__name__)


WEBDAV_ROOT = settings.HOOVER_NEXTCLOUD_URL + '/remote.php/dav/files'


def sync_nextcloud_directories(max_depth, max_size):
    users = get_user_model().objects.all()
    for user in users:
        if models.WebDAVPassword.objects.filter(user=user).exists():
            log.info(f'Found WebDAV-Password for user: {user.get_username()}')
            options = {
                'webdav_hostname': WEBDAV_ROOT + f'/{user.get_username()}',
                'webdav_login': user.get_username(),
                'webdav_password': models.WebDAVPassword.objects.get(user=user).password,
            }
            log.info(f'{options}')
            client = Client(options)
            log.info('Created webdav client!')
            directories = recurse_nextcloud_directories('/',
                                                        max_depth,
                                                        client,
                                                        user.get_username(),
                                                        max_size=max_size)
            log.info(f'Found directories: {directories}')
            for directory in directories:
                log.info(f'Creating directory: {directory}')
                models.NextcloudDirectory.objects.update_or_create(
                    name=get_name(directory['path']),
                    path=directory['path'],
                    modified=datetime.strptime(directory['modified'],
                                               '%a, %d %b %Y %H:%M:%S %Z'),
                    user=user
                )


def relative_path(path, username):
    return path.removeprefix(f'/remote.php/dav/files/{username}')


def get_name(path):
    return path.split('/')[-2]


def recurse_nextcloud_directories(path, max_depth, client, username, max_size=20, depth=0):
    # first element is the current directory itself
    content = client.list(path, get_info=True)[1:]
    log.info(f'Found root content: {[x.get("path") for x in content]}')
    directories = [x for x in content if x['isdir']]
    dir_list = []
    dir_list.extend(directories)

    if depth == max_depth:
        print('Reached max_depth!!!')
        return []
    if len(dir_list) > max_size:
        print('Dir list to long!!!')
        dir_list = dir_list[:max_size]
        return dir_list

    for directory in directories:
        # check if a directory with this path exists in the database
        # and if it was currently modified
        # if it wasn't modified we don't recurse it
        if models.NextcloudDirectory.objects.filter(path=directory['path']).exists():
            log.info('NextcloudDirectory exists in database!')
            modified = datetime.strptime(directory['modified'], '%a, %d %b %Y %H:%M:%S %Z')
            directory_in_db = models.NextcloudDirectory.objects.get(path=directory['path'])
            if modified == directory_in_db.modified:
                log.info('Directory has not been modified. Skipping.')
                continue

        new_content = recurse_nextcloud_directories(relative_path(directory['path'], username),
                                                    max_depth,
                                                    client,
                                                    username,
                                                    depth=depth + 1)
        print(f'new content: {[x.get("path") for x in new_content]}')
        if new_content:
            new_directories = [x for x in new_content if x['isdir']]
            if len(new_directories) + len(dir_list) > max_size:
                remaining = max_size - len(dir_list)
                new_directories = new_directories[:remaining]
                dir_list += new_directories
                print(f'added to dir_list: {new_directories}')
    print('dir_list:', [x["path"] for x in dir_list])
    return dir_list
