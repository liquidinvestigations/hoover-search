import os
from pathlib import Path
from urllib.parse import urlparse
import re

base_dir = Path(__file__).absolute().parent.parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

_hostname =  os.environ.get('HOOVER_HOSTNAME')
if _hostname:
    HOOVER_BASE_URL = 'https://' + _hostname
    ALLOWED_HOSTS = [_hostname]

def bool_env(value):
    return (value or '').lower() in ['on', 'true']

DEBUG = bool_env(os.environ.get('DEBUG'))

if bool_env(os.environ.get('HOOVER_TWOFACTOR_ENABLED')):
    from hoover.site.settings.common import INSTALLED_APPS
    from hoover.site.settings.common import MIDDLEWARE_CLASSES

    INSTALLED_APPS += (
        'hoover.contrib.twofactor',
        'django_otp',
        'django_otp.plugins.otp_totp',
        'hoover.contrib.ratelimit',
    )

    MIDDLEWARE_CLASSES += (
        'django_otp.middleware.OTPMiddleware',
        'hoover.contrib.twofactor.middleware.AutoLogout',
        'hoover.contrib.twofactor.middleware.RequireAuth',
    )

    _twofactor_invitation_valid = os.environ.get('HOOVER_TWOFACTOR_INVITATION_VALID')
    if _twofactor_invitation_valid:
        HOOVER_TWOFACTOR_INVITATION_VALID = int(_twofactor_invitation_valid)

    _twofactor_auto_logout = os.environ.get('HOOVER_TWOFACTOR_AUTOLOGOUT')
    if _twofactor_auto_logout:
        HOOVER_TWOFACTOR_AUTOLOGOUT = int(_twofactor_auto_logout)

    HOOVER_RATELIMIT_USER = (30, 60)  # 30 per minute
    HOOVER_TWOFACTOR_RATELIMIT = (3, 60)  # 3 per minute

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'search',
    },
}

# heroku-style db config
_db = os.environ.get('HOOVER_DB')
if _db:
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
