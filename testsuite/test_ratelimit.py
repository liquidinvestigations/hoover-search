from datetime import datetime, timedelta
import pytest
from django.utils.timezone import utc, now
from .fixtures import skip_twofactor, listen
from hoover.contrib.ratelimit import decorators

pytestmark = pytest.mark.django_db

@pytest.yield_fixture
def mock_time(monkeypatch):
    t = now()
    monkeypatch.setattr('hoover.contrib.ratelimit.models.time',
        lambda: t.timestamp())
    def set_time(value):
        nonlocal t
        assert t.tzinfo is utc
        t = value
    yield set_time

def test_rate_limit(skip_twofactor, mock_time):
    t0 = datetime(2016, 6, 13, 12, 0, 0, tzinfo=utc)

    class request:
        class user:
            get_username = staticmethod(lambda: 'john')

    @decorators.limit_user
    def func(r):
        return 'ok'

    def call(exception):
        rv = func(request)
        if rv == 'ok':
            assert not exception, "HttpLimitExceeded should have been returned"
        elif isinstance(rv, decorators.HttpLimitExceeded):
            assert exception, "HttpLimitExceeded should not have been returned"
        else:
            assert False, "unexpected return value %r" % rv

    mock_time(t0)
    for _ in range(30):
        call(False)

    for _ in range(10):
        call(True)

    mock_time(t0 + timedelta(minutes=1))
    for _ in range(20):
        call(False)

    mock_time(t0 + timedelta(minutes=2))
    for _ in range(20):
        call(False)
