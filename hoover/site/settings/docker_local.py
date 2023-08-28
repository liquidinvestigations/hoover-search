import os
import re
from logzero import logger as log

from .common import *  # noqa

base_dir = Path(__file__).absolute().parent.parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

_hostname = os.environ.get('HOOVER_HOSTNAME')
if _hostname:
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

if bool_env(os.environ.get('HOOVER_AUTHPROXY')):
    HOOVER_AUTHPROXY = True
    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.RemoteUserBackend',
    ]

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

SNOOP_BASE_URL = os.environ.get('SNOOP_BASE_URL')

HOOVER_ELASTICSEARCH_URL = os.environ.get('HOOVER_ES_URL')
HOOVER_TITLE = os.environ.get('HOOVER_TITLE', 'Hoover')
HOOVER_LIQUID_TITLE = os.environ.get('HOOVER_LIQUID_TITLE', 'Liquid')
HOOVER_LIQUID_URL = os.environ.get('HOOVER_LIQUID_URL', 'http://liquid')
HOOVER_HYPOTHESIS_EMBED = os.environ.get('HOOVER_HYPOTHESIS_EMBED')

DEBUG_WAIT_PER_COLLECTION = int(os.environ.get('DEBUG_WAIT_PER_COLLECTION', 0))

ES_MAX_CONCURRENT_SHARD_REQUESTS = int(
    os.environ.get('HOOVER_ES_MAX_CONCURRENT_SHARD_REQUESTS') or 3)


if bool_env(os.environ.get('USE_X_FORWARDED_HOST')):
    USE_X_FORWARDED_HOST = True

_secure_header = os.environ.get('SECURE_PROXY_SSL_HEADER')
if _secure_header:
    SECURE_PROXY_SSL_HEADER = (_secure_header, 'https')

if not DEBUG:
    # don't connect to the internet to verify my schema pls
    SWAGGER_SETTINGS = {
        'VALIDATOR_URL': None,
    }


log.info('hoover-search configuration loaded')
