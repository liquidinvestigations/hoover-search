from pathlib import Path
from hoover.site.settings.common import *

testsuite_dir = Path(__file__).absolute().parent

del ELASTICSEARCH_URL
SECRET_KEY = 'testing secret key'
HOOVER_UPLOADS_ROOT = str(testsuite_dir / 'uploads')

from hoover.site.settings.testing_local import *
