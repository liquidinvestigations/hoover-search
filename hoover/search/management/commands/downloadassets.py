import requests
from django.core.management.base import BaseCommand
from pathlib import Path

ASSETS = {
    'bootstrap.css':
        'https://cdn.rawgit.com/twbs/bootstrap/v4-dev/dist/css/bootstrap.css',
    'bootstrap.js':
        'https://cdn.rawgit.com/twbs/bootstrap/v4-dev/dist/js/bootstrap.js',
    'jquery.js':
        'https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.4/jquery.min.js',
}

class Command(BaseCommand):

    help = "Download assets"

    def handle(self, **options):
        appdir = Path(__file__).absolute().parent.parent.parent
        static = appdir / 'static' / 'search'
        static.mkdir(parents=True, exist_ok=True)

        for name, url in ASSETS.items():
            print(name)
            resp = requests.get(url)
            with (static / name).open('wb') as f:
                f.write(resp.content)

        print("Next, run `./manage.py collectstatic`")
