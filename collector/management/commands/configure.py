import yaml
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string
from ...models import Collection, Document


class Command(BaseCommand):

    help = "Imprt configuration file"

    def add_arguments(self, parser):
        parser.add_argument('config_path')

    def handle(self, verbosity, config_path, **options):
        with open(config_path) as f:
            config = yaml.load(f)
            for collection in config['collections']:
                loader_cls = import_string(collection['loader'])
                loader = loader_cls(**collection)

                (collection, _) = Collection.objects.get_or_create(
                    slug=collection['slug'])

                for data in loader.documents():
                    data['collection'] = collection
                    (doc, created) = Document.objects.get_or_create(
                        slug=data.pop('slug'),
                        defaults=data,
                    )
                    if created:
                        print '+++', doc.slug
                    else:
                        changed = False
                        for k in data:
                            if getattr(doc, k) != data[k]:
                                setattr(doc, k, data[k])
                                changed = True
                        if changed:
                            print '%%%', doc.slug
