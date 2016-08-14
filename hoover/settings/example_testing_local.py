from pathlib import Path

BASE_DIR = Path(__file__).absolute().parent.parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover',
    },
}

ELASTICSEARCH_URL = 'http://localhost:9200'

HOOVER_UPLOADS_ROOT = str(BASE_DIR / 'uploads')

FIXTURES_URL = 'http://localhost:8000'
