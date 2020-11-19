from .common import *  # noqa

SECRET_KEY = 'TODO_generate_random_string'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-search',
    },
}
HOOVER_ELASTICSEARCH_URL = 'http://localhost:9200'
