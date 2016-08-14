from pathlib import Path

base_dir = Path(__file__).absolute().parent.parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-search',
    },
}

ELASTICSEARCH_URL = 'http://localhost:9200'
HOOVER_UPLOADS_ROOT = str(base_dir / 'uploads')
