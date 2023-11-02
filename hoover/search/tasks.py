from . import celery as cel
from datetime import datetime
from django.conf import settings
import logging
from webdav3.client import Client
from django.contrib.auth import get_user_model
from . import models

log = logging.getLogger(__name__)

SYNC_KEY = 'hoover.search.nexctloudsync'

WEBDAV_ROOT = settings.HOOVER_NEXTCLOUD_URL + '/remote.php/dav/files'


@cel.app.task(bind=True, queue=SYNC_KEY, name=SYNC_KEY, max_retries=None)
def sync_nextcloud_directories_task():
    log.warning('Running periodic task to sync nextcloud directories!')
    sync_nextcloud_directories()


def sync_nextcloud_directories():
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
            directories = recurse_nextcloud_directories('/', 4, client, user.get_username())
            log.info(f'Found directories: {directories}')
            for directory in directories:
                log.info(f'Creating directory: {directory}')
                models.NextcloudDirectory.objects.get_or_create(
                    name=get_name(directory['path']),
                    path=directory['path'],
                    modified=datetime.strptime(directory['modified'],
                                               '%a, %d %b %Y %H:%M:%S %Z'),
                    user=user
                )


def relative_path(path, username):
    return path.removeprefix(f'/remote.php/dav/files/{username}')


def full_path(path, username):
    return f'/remote.php/dav/files/{username}' + path


def get_name(path):
    return path.split('/')[-2]


def recurse_nextcloud_directories(path, max_depth, client, username, max_size=20, depth=0):
    content = client.list(path, get_info=True)
    log.info(f'Found root content: {content}')
    directories = [x for x in content if x['isdir']]
    dir_list = []
    dir_list.extend(directories)

    if depth == max_depth:
        return []
    if len(dir_list) > max_size:
        dir_list = dir_list[:max_size]
        return dir_list

    for directory in directories:
        # skip if directory is itself
        if directory['path'] == full_path(path, username):
            continue
        # check if a directory with this path exists in the database
        # and if it was currently modified
        # if it wasn't modified we don't recurse it
        if models.NextcloudDirectory.objects.filter(path=directory['path']).exists():
            modified = datetime.strptime(directory['modified'], '%a, %d %b %Y %H:%M:%S %Z')
            directory_in_db = models.NextcloudDirectory.objects.get(path=directory['path'])
            if modified == directory_in_db.modified:
                continue
        else:
            new_content = recurse_nextcloud_directories(relative_path(directory['path'], username),
                                                        max_depth,
                                                        client,
                                                        username,
                                                        depth=depth + 1)
            if new_content:
                new_directories = [x for x in new_content if x['isdir']]
                if len(new_directories) + len(dir_list) > max_size:
                    remaining = max_size - len(dir_list)
                    new_directories = new_directories[:remaining]
                    dir_list += new_directories
    return dir_list
