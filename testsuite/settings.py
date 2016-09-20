from pathlib import Path
from hoover.site.settings.common import *

INSTALLED_APPS = INSTALLED_APPS + (
    'hoover.contrib.twofactor',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'hoover.contrib.ratelimit',
)

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'django_otp.middleware.OTPMiddleware',
    'hoover.contrib.twofactor.middleware.AutoLogout',
    'hoover.contrib.twofactor.middleware.RequireAuth',
)

testsuite_dir = Path(__file__).absolute().parent

del ELASTICSEARCH_URL
SECRET_KEY = 'testing secret key'
HOOVER_UPLOADS_ROOT = str(testsuite_dir / 'uploads')
HOOVER_BASE_URL = 'http://testserver'

from hoover.site.settings.testing_local import *
