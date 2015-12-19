"""
This is an example settings file. Copy it to `local.py`.
"""
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEBUG = True
SECRET_KEY = 'something random'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',

        # Database info.
        # see: https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-DATABASES
        'NAME': 'hoover',
    },
}

STATIC_ROOT = BASE_DIR + '/static'
HOOVER_UPLOADS_ROOT = BASE_DIR + '/uploads'
