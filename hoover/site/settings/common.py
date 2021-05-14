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
    'hoover.contrib.ratelimit',
    'rest_framework',
    'drf_yasg',
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
                'hoover.search.context_processors.default',
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
HOOVER_BATCH_LIMIT = 250
HOOVER_EVENTS_DIR = None

HOOVER_OAUTH_LIQUID_URL = None
HOOVER_OAUTH_LIQUID_CLIENT_ID = None
HOOVER_OAUTH_LIQUID_CLIENT_SECRET = None

HOOVER_AUTHPROXY = False

HOOVER_HYPOTHESIS_EMBED_URL = None

ES_BATCHED_REDUCE_SIZE = 30
ES_MAX_CONCURRENT_SHARD_REQUESTS = 3
ES_BATCH_MAX_CONCURRENT_SEARCHES = 4
