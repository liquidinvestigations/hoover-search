from datetime import datetime
from django.conf import settings
from django.utils.timezone import make_aware, now
import logging
from webdav3.client import Client
from django.contrib.auth import get_user_model
from . import models

log = logging.getLogger(__name__)


WEBDAV_ROOT = settings.HOOVER_NEXTCLOUD_URL + '/remote.php/dav/files'


def sync_nextcloud_directories(max_depth, max_size, purge=False):
    users = get_user_model().objects.all()
    for user in users:
        if models.WebDAVPassword.objects.filter(user=user).exists():
            options = {
                'webdav_hostname': WEBDAV_ROOT + f'/{user.get_username()}',
                'webdav_login': user.get_username(),
                'webdav_password': models.WebDAVPassword.objects.get(user=user).password,
            }
            client = Client(options)
            directories = recurse_nextcloud_directories('/',
                                                        max_depth,
                                                        client,
                                                        user.get_username(),
                                                        max_size=max_size,
                                                        get_all=purge)
            log.info(f'Found directories: {directories}')

            if purge:
                all_db_directories = models.NextcloudDirectory.objects.all()
                found_directories_paths = [x['path'] for x in directories]
                for db_directory in all_db_directories:
                    if db_directory.path not in found_directories_paths:
                        log.info(f'"{db_directory}" was deleted from Nextcloud. Marking it as deleted.')
                        db_directory.deleted_from_nextcloud = now()
                        db_directory.save()

            for directory in directories:
                log.info(f'Creating directory: {directory}')
                modified = datetime.strptime(directory['modified'],
                                             '%a, %d %b %Y %H:%M:%S %Z')
                modified = make_aware(modified)
                models.NextcloudDirectory.objects.update_or_create(
                    path=directory['path'],
                    defaults={
                        'name': get_name(directory['path']),
                        'modified': modified,
                        'user': user,
                        'deleted_from_nextcloud': None,
                    }
                )


def relative_path(path, username):
    return path.removeprefix(f'/remote.php/dav/files/{username}')


def get_name(path):
    return path.split('/')[-2]


def recurse_nextcloud_directories(path, max_depth, client, username, max_size=20, depth=0, get_all=False):
    # first element is the current directory itself
    content = client.list(path, get_info=True)[1:]
    directories = [x for x in content if x['isdir']]
    dir_list = []
    dir_list.extend(directories)

    if depth == max_depth:
        return []
    if len(dir_list) > max_size:
        dir_list = dir_list[:max_size]
        return dir_list

    for directory in directories:
        # check if a directory with this path exists in the database
        # and if it was currently modified
        # if it wasn't modified we don't recurse it
        if models.NextcloudDirectory.objects.filter(path=directory['path']).exists():
            log.info('NextcloudDirectory exists in database!')
            modified = datetime.strptime(directory['modified'], '%a, %d %b %Y %H:%M:%S %Z')
            # make timezone aware
            # nextcloud returns time in GMT timezone
            modified = make_aware(modified)
            directory_in_db = models.NextcloudDirectory.objects.get(path=directory['path'])
            # skip directories that have not been modified if get_all is not set
            if get_all is not True and modified == directory_in_db.modified:
                log.info('Directory has not been modified. Skipping.')
                continue

        new_content = recurse_nextcloud_directories(relative_path(directory['path'], username),
                                                    max_depth,
                                                    client,
                                                    username,
                                                    max_size=max_size,
                                                    depth=depth + 1,
                                                    get_all=get_all)
        if new_content:
            new_directories = [x for x in new_content if x['isdir']]
            if len(new_directories) + len(dir_list) > max_size:
                remaining = max_size - len(dir_list)
                new_directories = new_directories[:remaining]
            dir_list += new_directories
    return dir_list
