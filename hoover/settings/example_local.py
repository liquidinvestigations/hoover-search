from pathlib import Path
from .common import cdn_assets

base_dir = Path(__file__).absolute().parent.parent.parent

SECRET_KEY = 'something random'
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-search',
    },
}
STATIC_ROOT = str(base_dir / 'static')
HOOVER_UPLOADS_ROOT = str(base_dir / 'uploads')
HOOVER_ASSETS = cdn_assets
