from .common import *  # noqa

# To enable two-factor authentication and rate limiting see:
# github.com/hoover/search/tree/master/hoover/contrib/twofactor#readme
# github.com/hoover/search/tree/master/hoover/contrib/ratelimit#readme

SECRET_KEY = 'TODO_generate_random_string'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-search',
    },
}
HOOVER_ELASTICSEARCH_URL = 'http://localhost:9200'
