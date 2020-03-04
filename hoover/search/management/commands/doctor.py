from pathlib import Path
import re
import sys
import urllib.request
import urllib.error
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from ...models import Collection
from ...es import elasticsearch


def http_get_content(link):
    try:
        with urllib.request.urlopen(link) as content:
            return content.read()
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None


class Command(BaseCommand):
    help = "Sanity check for search. Run with no arguments."

    def handle(self, *args, **options):
        checkers = [
            ('python', self.check_python, False),
            ('database', self.check_database, False),
            ('elasticsearch', self.check_es, False),
            ('events_dir', self.check_events_dir, settings.HOOVER_EVENTS_DIR is None)
        ]

        checkers += self.get_collection_checkers()

        have_errors = False
        for name, check_fun, skip in checkers:
            if skip:
                self.print_message("Skipping the check for " + name + ".")
            else:
                self.print_message("Checking " + name + ".")
                result = check_fun()
                if result:
                    self.print_success(' ' * 9 + name + " ok.")
                else:
                    have_errors = True
                    self.print_error(name + " failed the check.")
            self.print_message('')

        if not have_errors:
            self.print_message("Checking all external collections.")
            for name, check_fun, collection in self.get_collection_checkers():
                collection_string = "{}: '{}'".format(collection.id, collection.name)
                self.print_message("  Checking   " + collection_string)
                result = check_fun()
                if result:
                    self.print_success("  Collection " + collection_string + " is ok.")
                else:
                    have_errors = True
                    self.print_error("  Collection " + collection_string + " has failed a check.")
                self.print_message('')

        if have_errors:
            self.print_error("The setup has failed some checks.")
            self.print_error("For more information please see")
            self.print_error("https://github.com/hoover/search/blob/master/Readme.md")
            sys.exit(1)
        else:
            self.print_success("All checks have passed.")

    def check_python(self):
        if sys.version_info[0] != 3 or sys.version_info[1] < 5:
            self.print_error("The Python version supplied is {}.".format(sys.version))
            self.print_error("Hoover needs at least Python 3.5 to work.")
            self.print_error("Please use a supported version of Python.")
            return False
        return True

    def check_database(self):
        db_conn = connections['default']
        try:
            _ = db_conn.cursor()
        except OperationalError:
            self.print_error("The database settings are not valid.")
            self.print_error("Please check the database access data under DATABASES.")
            return False
        return True

    def check_es(self):
        es_link = settings.HOOVER_ELASTICSEARCH_URL
        content = http_get_content(es_link)

        if not content:
            self.print_error("Could not connect to elasticsearch using")
            self.print_error("the link supplied in HOOVER_ELASTICSEARCH_URL.")
            return False

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            self.print_error("elasticsearch's response could not be decoded.")
            self.print_error("Please restart the elasticsearch server and try again.")
            return False

        version_string = data['version']['number']
        version_string = re.sub(r'[^\d\.]+', '', version_string)
        version = tuple(int(x) for x in version_string.split('.'))

        if version[0] != 2:
            self.print_error("elasticsearch is version {}, but".format(version))
            self.print_error("Hoover needs elasticsearch to version 2.*.")
            return False
        return True

    def check_events_dir(self):
        events_dir = settings.HOOVER_EVENTS_DIR
        if not Path(events_dir).exists() or not Path(events_dir).is_dir():
            self.print_error("The path supplied in HOOVER_EVENTS_DIR is not a valid folder.")
            return False
        return True

    def get_collection_checkers(self):
        collections = Collection.objects.all()
        return [
            (
                "collection " + collection.name,
                lambda: self.check_collection(collection),
                collection,
            )
            for collection in collections
            if collection.loader == 'hoover.search.loaders.external.Loader']

    def check_collection(self, collection):
        with elasticsearch() as es:
            good_index = es.indices.exists(collection.index)
        try:
            options = json.loads(collection.options)
        except json.JSONDecodeError:
            self.print_error("  The option string for collection {}".format(collection.name))
            self.print_error("  is not valid JSON.")
            return False

        if 'url' not in options:
            self.print_error("  The option string for collection {}".format(collection.name))
            self.print_error('  does not have the "url" key set.')
            return False
        else:
            good_endpoint = self.check_external_collection_endpoint(options['url'])
        return good_index and good_endpoint

    def check_external_collection_endpoint(self, url):
        content = http_get_content(url)
        if not content:
            self.print_error("  Could not connect to the collection endpoint at {}".format(url))
            return False
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            self.print_error("  The endpoint at {} did not return valid json.".format(url))
            return False
        if 'feed' not in data:
            self.print_error('  The endpoint at {} did not return a value for the "feed" key'.format(url))
            return False
        return True

    def print_error(self, string):
        self.stdout.write(self.style.ERROR(string))

    def print_message(self, string):
        self.stdout.write(string)

    def print_success(self, string):
        self.stdout.write(self.style.SUCCESS(string))
