from pathlib import Path
from . import common

base_dir = Path(__file__).absolute().parent.parent.parent.parent

# To enable two-factor authentication and rate limiting see:
# github.com/hoover/search/tree/master/hoover/contrib/twofactor#readme
# github.com/hoover/search/tree/master/hoover/contrib/ratelimit#readme

SECRET_KEY = TODO_generate_random_string
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-search',
    },
}
STATIC_ROOT = str(base_dir / 'static')
HOOVER_UPLOADS_ROOT = str(base_dir / 'uploads')
HOOVER_ASSETS = common.cdn_assets
