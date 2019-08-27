import os
import re
from logzero import logger as log

from .common import *

base_dir = Path(__file__).absolute().parent.parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

_hostname =  os.environ.get('HOOVER_HOSTNAME')
if _hostname:
    HOOVER_BASE_URL = 'https://' + _hostname
    ALLOWED_HOSTS = [_hostname]

def bool_env(value):
    return (value or '').lower() in ['on', 'true']

DEBUG = bool_env(os.environ.get('DEBUG'))
if DEBUG:
    log.warn('DEBUG mode on')

env_ratelimit = os.environ.get('HOOVER_RATELIMIT_USER', '30,60')
if len(env_ratelimit.split(',')) != 2:
    raise RuntimeError(f'Invalid environment variable HOOVER_RATELIMIT_USER: "{env_ratelimit}"')
HOOVER_RATELIMIT_USER = [int(x) for x in env_ratelimit.split(',')]

if bool_env(os.environ.get('HOOVER_TWOFACTOR_ENABLED')):
    INSTALLED_APPS += (
        'hoover.contrib.twofactor',
        'django_otp',
        'django_otp.plugins.otp_totp',
    )

    MIDDLEWARE_CLASSES += (
        'django_otp.middleware.OTPMiddleware',
        'hoover.contrib.twofactor.middleware.AutoLogout',
        'hoover.contrib.twofactor.middleware.RequireAuth',
    )

    log.info("Enabling 2FA")

    _twofactor_invitation_valid = os.environ.get('HOOVER_TWOFACTOR_INVITATION_VALID')
    if _twofactor_invitation_valid:
        HOOVER_TWOFACTOR_INVITATION_VALID = int(_twofactor_invitation_valid)

    _twofactor_auto_logout = os.environ.get('HOOVER_TWOFACTOR_AUTOLOGOUT')
    if _twofactor_auto_logout:
        HOOVER_TWOFACTOR_AUTOLOGOUT = int(_twofactor_auto_logout)

    HOOVER_TWOFACTOR_RATELIMIT = (3, 60)  # 3 per minute

if os.environ.get('LIQUID_AUTH_CLIENT_ID'):
    INSTALLED_APPS += (
        'hoover.contrib.oauth2',
    )

    LIQUID_AUTH_PUBLIC_URL = os.environ.get('LIQUID_AUTH_PUBLIC_URL')
    LIQUID_AUTH_INTERNAL_URL = os.environ.get('LIQUID_AUTH_INTERNAL_URL')
    LIQUID_AUTH_CLIENT_ID = os.environ.get('LIQUID_AUTH_CLIENT_ID')
    LIQUID_AUTH_CLIENT_SECRET = os.environ.get('LIQUID_AUTH_CLIENT_SECRET')

    log.info("Enabling Liquid OAuth2 at %s", LIQUID_AUTH_PUBLIC_URL)

if bool_env(os.environ.get('HOOVER_AUTHPROXY')):
    HOOVER_AUTHPROXY = True
    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.RemoteUserBackend',
    ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'search',
    },
}

# heroku-style db config
_db = os.environ['HOOVER_DB']
dbm = re.match(
    r'postgresql://(?P<user>[^:]+):(?P<password>[^@]+)'
    r'@(?P<host>[^:]+):(?P<port>\d+)/(?P<name>.+)',
    _db,
)
if not dbm:
    raise RuntimeError("Can't parse HOOVER_DB value %r" % _db)
DATABASES['default']['HOST'] = dbm.group('host')
DATABASES['default']['PORT'] = dbm.group('port')
DATABASES['default']['NAME'] = dbm.group('name')
DATABASES['default']['USER'] = dbm.group('user')
DATABASES['default']['PASSWORD'] = dbm.group('password')

STATIC_ROOT = str(base_dir / 'static')

HOOVER_UPLOADS_ROOT = str(base_dir / 'uploads')
HOOVER_UI_ROOT = str(base_dir.parent / 'ui' / 'build')
HOOVER_EVENTS_DIR = str(base_dir.parent / 'metrics' / 'users')
HOOVER_ELASTICSEARCH_URL = os.environ.get('HOOVER_ES_URL')
HOOVER_TITLE = os.environ.get('HOOVER_TITLE', 'Hoover')
HOOVER_HYPOTHESIS_EMBED = os.environ.get('HOOVER_HYPOTHESIS_EMBED')


if bool_env(os.environ.get('USE_X_FORWARDED_HOST')):
    USE_X_FORWARDED_HOST = True

_secure_header = os.environ.get('SECURE_PROXY_SSL_HEADER')
if _secure_header:
    SECURE_PROXY_SSL_HEADER = (_secure_header, 'https')

log.info('hoover-search configuration loaded')
