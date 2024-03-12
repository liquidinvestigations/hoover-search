import os
import re
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.apps import apps


def validate_collection_name(name):
    if not complies_with_naming_rules(name):
        raise ValidationError(
            f'"{name}" is not a valid name. Collection names need to be lowercase alphanumeric and at least 3 letters.')
    if not no_existing_collection_in_db(name):
        raise ValidationError(
            f'"{name}" already exists in the Collection or NextcloudCollection database.'
        )
    if not no_collisions_with_snoop_resources(name):
        raise ValidationError(
            f'"{name}" collides with an index name of a snoop resource (elasticsearch, s3 buckets or database table).'
        )


def validate_directory_path(directory_id):
    NextcloudDirectory = apps.get_model('search', 'NextcloudDirectory')
    directory = NextcloudDirectory.objects.get(pk=directory_id)
    if not parent_not_in_collection(directory.path):
        raise ValidationError(
            f'"{directory.path}" is already indexed by another collection through a parent directory.'
        )


def complies_with_naming_rules(name):
    search_forbidden_char = re.compile(r'[^a-z0-9-]').search

    if search_forbidden_char(name):
        return False

    if len(name) < 3 or len(name) > 63:
        return False
    return True


def no_existing_collection_in_db(name):
    Collection = apps.get_model('search', 'Collection')
    NextcloudCollection = apps.get_model('search', 'NextcloudCollection')
    existing_names = []
    collections = Collection.objects.all()
    nextcloud_collections = NextcloudCollection.objects.all()
    existing_names += [collection.name for collection in collections]
    existing_names += [nccollection.name for nccollection in nextcloud_collections]
    if name in existing_names:
        return False
    return True


def no_collisions_with_snoop_resources(name):
    validation_url = settings.SNOOP_BASE_URL + '/common/validate_new_collection_name'
    payload = {
        'name': name,
    }
    res = requests.post(validation_url, json=payload)
    is_valid = res.json().get('valid')
    return is_valid


def parent_not_in_collection(path):
    NextcloudCollection = apps.get_model('search', 'NextcloudCollection')
    prefix = '/remote.php/dav/files'
    unique_path = path.removeprefix(prefix).rstrip("/")
    while unique_path != '/':
        full_path = prefix + unique_path + '/'
        if NextcloudCollection.objects.filter(directory__path=full_path).exists():
            return False
        unique_path = os.path.dirname(unique_path)
    return True
