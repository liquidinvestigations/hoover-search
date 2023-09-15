from pathlib import Path
from hoover.site.settings.common import *

CELERY_TASK_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


testsuite_dir = Path(__file__).absolute().parent

SECRET_KEY = 'testing secret key'
HOOVER_BASE_URL = 'http://testserver'
HOOVER_RATELIMIT_USER = (30, 5)  # 30 per 5s
HOOVER_RATELIMIT_THUMBNAIL = (50, 5)  # 50 per 5s

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
