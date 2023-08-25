import os
from pathlib import Path

base_dir = Path(__file__).absolute().parent.parent.parent.parent

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hoover.search',
    'hoover.upload.apps.UploadConfig',
    'rest_framework',
    'drf_yasg',
    'django_celery_results',
    'django_tus',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'hoover.search.middleware.AuthproxyUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'hoover.search.middleware.NoReferral',
    'hoover.search.middleware.NoCache',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'hoover.search.middleware.PdfPageSplitterMiddleware',
]

ROOT_URLCONF = 'hoover.site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'logfile': {
            'format': ('%(asctime)s %(process)d '
                       '%(levelname)s %(name)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'loggers': {
        'django.request': {
            'level': 'WARNING',
            'propagate': False,
            'handlers': ['stderr'],
        },
        'hoover.search': {
            'level': 'INFO',
            'propagate': False,
            'handlers': ['stderr'],
        },
        'hoover.upload': {
            'level': 'INFO',
            'propagate': False,
            'handlers': ['stderr'],
        },
        '': {
            'level': 'WARNING',
            'propagate': True,
            'handlers': ['stderr'],
        },
    },
    'handlers': {
        'stderr': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'logfile',
        },
    },
}

WSGI_APPLICATION = 'hoover.site.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'

X_FRAME_OPTIONS = 'SAMEORIGIN'
CSRF_HEADER_NAME = "HTTP_X_HOOVER_CSRFTOKEN"
CSRF_COOKIE_NAME = "hoover-csrftoken"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

OTP_TOTP_SYNC = False

HOOVER_ELASTICSEARCH_URL = 'http://localhost:9200'

HOOVER_TITLE = 'Hoover'
HOOVER_LIQUID_TITLE = "Liquid"
HOOVER_LIQUID_URL = 'http://liquid'
HOOVER_HYPOTHESIS_EMBED = None

STATIC_ROOT = str(base_dir / 'static')

HOOVER_LOADERS = [
    'hoover.search.loaders.external.Loader',
]

HOOVER_PDFJS_URL = None

TIKA_URL = 'http://localhost:9998'

EMBED_HYPOTHESIS = None

_minute = 60
_hour = 60 * _minute
HOOVER_TWOFACTOR_INVITATION_VALID = 30  # minutes
HOOVER_TWOFACTOR_AUTOLOGOUT = 3 * _hour
HOOVER_TWOFACTOR_RATELIMIT = None
HOOVER_RATELIMIT_USER = None
HOOVER_RATELIMIT_THUMBNAIL = (1000, 60)
HOOVER_BATCH_LIMIT = 10000
HOOVER_EVENTS_DIR = None

HOOVER_OAUTH_LIQUID_URL = None
HOOVER_OAUTH_LIQUID_CLIENT_ID = None
HOOVER_OAUTH_LIQUID_CLIENT_SECRET = None

HOOVER_AUTHPROXY = False

HOOVER_HYPOTHESIS_EMBED_URL = None

DEBUG_WAIT_PER_COLLECTION = 0

ES_BATCHED_REDUCE_SIZE = 30
ES_MAX_CONCURRENT_SHARD_REQUESTS = 3
ES_BATCH_MAX_CONCURRENT_SEARCHES = 4

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_RESULT_BACKEND = 'django-db'

HOOVER_CELERY_SEARCH_QUEUES = ['hoover.search.search', 'hoover.search.upload']
HOOVER_CELERY_BATCH_QUEUES = ['hoover.search.batch_search']

SEARCH_WORKER_COUNT = 1
CELERY_BROKER_URL = os.getenv('SEARCH_AMQP_URL')

SNOOP_FORWARD_HEADERS = [
    'Content-Disposition', 'Accept-Ranges', 'Content-Range', 'Content-Length', 'Content-Type',
    'Cache-Control', 'Date', 'Expires', 'Vary', "ETag"]

SNOOP_COLLECTION_DIR = Path(os.getenv('SNOOP_COLLECTION_DIR', '/opt/hoover/collections'))

# all django_tus related settings can be found here: https://github.com/alican/django-tus

# this is where django_tus saves the resumable uploads
TUS_UPLOAD_DIR = Path(os.getenv('TUS_UPLOAD_DIR', '/alloc/tmp/tus/uploads'))

# this is where django_tus moves the finished uploads. We use the signal that is sent after an upload
# is finished to move it from there into the correct collection.
TUS_DESTINATION_DIR = Path(os.getenv('TUS_DESTINATION_DIR', '/alloc/tmp/tus/files'))

TUS_FILE_NAME_FORMAT = 'increment'  # Other options are: 'random-suffix', 'random', 'keep'
TUS_EXISTING_FILE = 'error'  # Other options are: 'overwrite',  'error', 'rename'

# 5 MB in bytes, this needs to be higher than the chunksize of the tus client.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 2**20

if os.getenv('SENTRY_DSN'):
    import sentry_sdk
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    SENTRY_SAMPLE_RATE = float(os.getenv('SENTRY_SAMPLE_RATE', '1.0'))
    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=SENTRY_SAMPLE_RATE)
