import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECRET_KEY = 'something random'
DEBUG = True
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql_psycopg2',
#        'NAME': 'hoover',
#    },
#}
STATIC_ROOT = BASE_DIR + '/static'
HOOVER_UPLOADS_ROOT = BASE_DIR + '/uploads'
