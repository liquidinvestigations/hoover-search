INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hoover.search',
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'hoover.search.middleware.NoReferral',
    'hoover.search.middleware.NoCache',
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
LOGIN_REDIRECT_URL = 'home'

ELASTICSEARCH_URL = 'http://localhost:9200'

HOOVER_UPLOADS_URL = '/uploads/'

HOOVER_LOADERS = [
    'hoover.search.loaders.upload.Loader',
    'hoover.search.loaders.webdav.Loader',
    'hoover.search.loaders.collectible.Loader',
    'hoover.search.loaders.external.Loader',
]

HOOVER_PDFJS_URL = None

TIKA_URL = 'http://localhost:9998'

EMBED_HYPOTHESIS = None

cdn_assets = {
    'bootstrap_css': ('https://cdn.rawgit.com/twbs/bootstrap/v4-dev/dist/'
        'css/bootstrap.css'),
    'bootstrap_js': ('https://cdn.rawgit.com/twbs/bootstrap/v4-dev/dist/'
        'js/bootstrap.js'),
    'jquery_js': ('https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.4/'
        'jquery.min.js'),
}
