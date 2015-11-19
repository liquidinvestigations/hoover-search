from datetime import datetime
from django.utils.timezone import UTC


def now():
    return datetime.utcnow().replace(tzinfo=UTC())
