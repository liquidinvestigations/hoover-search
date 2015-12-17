INSTALLED_APPS = (
    'collector',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'hoover.urls'

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
        'collector': {
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

WSGI_APPLICATION = 'hoover.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
LOGIN_REDIRECT_URL = 'home'

ELASTICSEARCH_URL = 'http://localhost:9200'

HOOVER_UPLOADS_URL = '/uploads/'
