from pathlib import Path
from hoover.site.settings.common import *


testsuite_dir = Path(__file__).absolute().parent

SECRET_KEY = 'testing secret key'
HOOVER_UI_ROOT = str(testsuite_dir / 'mock_ui')
HOOVER_BASE_URL = 'http://testserver'
HOOVER_RATELIMIT_USER = (30, 60)  # 30 per minute

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'search',
        'USER': 'search',
        'PASSWORD': 'search',
        'HOST': 'search-pg',
        'PORT': 5432,
    },
}

HOOVER_ELASTICSEARCH_URL = 'http://search-es:9200'
