from pathlib import Path
from . import common

base_dir = Path(__file__).absolute().parent.parent.parent.parent

## to enable two-factor authentication:
#INSTALLED_APPS = common.INSTALLED_APPS + (
#    'hoover.contrib.twofactor',
#    'django_otp',
#    'django_otp.plugins.otp_totp',
#)
#MIDDLEWARE_CLASSES = common.MIDDLEWARE_CLASSES + (
#    'django_otp.middleware.OTPMiddleware',
#    'hoover.contrib.twofactor.middleware.RequireAuth',
#)

## to enable rate limiting for searches and downloads:
#INSTALLED_APPS = common.INSTALLED_APPS + (
#    'hoover.contrib.ratelimit',
#)

SECRET_KEY = 'something random'
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-search',
    },
}
STATIC_ROOT = str(base_dir / 'static')
HOOVER_UPLOADS_ROOT = str(base_dir / 'uploads')
HOOVER_ASSETS = common.cdn_assets
