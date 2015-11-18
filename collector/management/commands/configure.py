import yaml
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string


class Command(BaseCommand):

    help = "Imprt configuration file"

    def add_arguments(self, parser):
        parser.add_argument('config_path')

    def handle(self, verbosity, config_path, **options):
        with open(config_path) as f:
            config = yaml.load(f)
            for collection in config['collections']:
                loader_cls = import_string(collection['loader'])
                loader = loader_cls(**config)
