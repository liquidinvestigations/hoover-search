from pathlib import Path
from hoover.site.settings.common import *


testsuite_dir = Path(__file__).absolute().parent

SECRET_KEY = 'testing secret key'
HOOVER_BASE_URL = 'http://testserver'
HOOVER_RATELIMIT_USER = (30, 60)  # 30 per minute
HOOVER_RATELIMIT_THUMBNAIL = (50, 60)

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
SNOOP_BASE_URL = 'http://example.com'
