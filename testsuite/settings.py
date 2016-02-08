from hoover.settings.common import *

del ELASTICSEARCH_URL
SECRET_KEY = 'testing secret key'
ELASTICSEARCH_INDEX_PREFIX = 'hoovertest-'

from hoover.settings.testing_local import *
