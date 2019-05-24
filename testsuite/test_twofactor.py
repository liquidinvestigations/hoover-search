# TODO make sure signals are sent

from datetime import datetime, timedelta
import pytest
from django.utils.timezone import utc, now
from django_otp.oath import hotp
from django_otp.plugins.otp_totp.models import TOTPDevice
from hoover.contrib.twofactor import invitations, models, signals
from .fixtures import listen

pytestmark = pytest.mark.django_db

INVITATION_DURATION = 30 # minutes

@pytest.yield_fixture
def mock_time(monkeypatch):
    class mock_time:
        time = staticmethod(lambda: t.timestamp())
    t = now()
    patch = monkeypatch.setattr
    patch('hoover.contrib.twofactor.invitations.now', lambda: t)
    patch('hoover.contrib.twofactor.middleware.time', mock_time.time)
    patch('hoover.contrib.ratelimit.models.time', mock_time.time)
    patch('django_otp.plugins.otp_totp.models.time', mock_time)
    def set_time(value):
        nonlocal t
        assert t.tzinfo is utc
        t = value
    yield set_time

def _totp(device, now):
    counter = int(now.timestamp() - device.t0) // device.step
    return hotp(device.bin_key, counter)

def _access_homepage(client):
    resp = client.get('/', follow=False)
    if resp.status_code == 200:
        content = b''.join(resp.streaming_content).decode('utf-8')
        assert content == 'hoover ui homepage\n'
        return True
    elif resp.status_code == 302:
        return False
    else:
        raise RuntimeError("unexpected response %r" % resp)

@pytest.mark.parametrize(
    'minutes,username_ok,password_ok,code_ok,invitation,success',
    [
        (10, True, True, True, True, True),
        (40, True, True, True, False, False),
        (10, False, True, True, True, False),
        (10, True, False, True, True, False),
        (10, True, True, False, True, False),
    ])
def test_flow(client, listen,
        mock_time, minutes, username_ok, password_ok, code_ok,
        invitation, success):

    invitation_open = listen(signals.invitation_open)
    invitation_accept = listen(signals.invitation_accept)

    t0 = datetime(2016, 6, 13, 12, 0, 0, tzinfo=utc)
    t1 = t0 + timedelta(minutes=minutes)

    mock_time(t0)
    url = invitations.invite('john', INVITATION_DURATION, create=True)
    assert not _access_homepage(client)

    mock_time(t1)
    client.get(url)

    if not invitation:
        assert TOTPDevice.objects.count() == 0
        return

    assert invitation_open == [{'username': 'john'}]

    [device] = TOTPDevice.objects.all()
    hour = timedelta(hours=1)
    resp = client.post(url, {
        'username': 'john' if username_ok else 'ramirez',
        'password': 'secretz',
        'password-confirm': 'secretz' if password_ok else 'foobar',
        'code': _totp(device, t1) if code_ok else _totp(device, t1 + hour),
    })

    if success:
        assert invitation_accept == [{'username': 'john'}]
        assert "Verification successful." in resp.content.decode('utf-8')
        assert _access_homepage(client)

    else:
        assert invitation_accept == []
        assert not _access_homepage(client)

def _accept(client, invitation, password, mock_now=None):
    client.get(f'/invitation/{invitation.code}')
    [device] = invitation.user.totpdevice_set.all()

    resp = client.post(f'/invitation/{invitation.code}', {
        'username': invitation.user.username,
        'password': password,
        'password-confirm': password,
        'code': _totp(device, mock_now or now()),
    })
    assert "Verification successful." in resp.content.decode('utf8')

    device.refresh_from_db()
    return device


def _reset_last_use(device):
    device.refresh_from_db()
    device.last_t = -1
    device.save()


@pytest.mark.parametrize('username,password,interval,success', [
    ('john', 'pw', timedelta(0), True),
    ('john', 'pw', timedelta(minutes=2), False),
    ('johnny', 'pw', timedelta(0), False),
    ('john', 'pwz', timedelta(0), False),
])
def test_login(client, listen, username, password, interval, success):
    login_failure = listen(signals.login_failure)
    invitations.invite('john', INVITATION_DURATION, create=True)
    device = _accept(client, models.Invitation.objects.get(), 'pw')
    assert _access_homepage(client)
    client.logout()
    _reset_last_use(device)
    assert not _access_homepage(client)
    client.post('/accounts/login/', {
        'username': username,
        'password': password,
        'otp_token': _totp(device, now() + interval),
    })
    if success:
        assert login_failure == []
        assert _access_homepage(client)
    else:
        assert login_failure == [{'otp_failure': bool(interval)}]
        assert not _access_homepage(client)

def test_auto_logout(client, mock_time, listen):
    auto_logout = listen(signals.auto_logout)
    t0 = datetime(2016, 6, 13, 12, 0, 0, tzinfo=utc)

    mock_time(t0)
    invitations.invite('john', INVITATION_DURATION, create=True)
    device = _accept(client, models.Invitation.objects.get(), 'pw', t0)
    assert _access_homepage(client)

    mock_time(t0 + timedelta(hours=2, minutes=59))
    assert auto_logout == []
    assert _access_homepage(client)

    mock_time(t0 + timedelta(hours=3, minutes=0, seconds=5))
    assert not _access_homepage(client)
    assert auto_logout == [{'username': 'john'}]

def test_rate_limit(client, mock_time, listen):
    rate_limit_exceeded = listen(signals.rate_limit_exceeded)
    t0 = datetime(2016, 6, 13, 12, 0, 0, tzinfo=utc)
    now = None

    def set_time(t):
        nonlocal now
        now = t
        mock_time(t)

    def try_login(correct_otp, expect_limit, expect_success):
        device.last_t = -1
        device.save()
        otp_token = _totp(device, now) if correct_otp else '123456'
        resp = client.post('/accounts/login/', {
            'username': 'john',
            'password': 'pw',
            'otp_token': otp_token,
        })
        html = resp.content.decode('utf8')
        is_rate_limit = 'Your account is temporarily locked' in html
        assert expect_limit == is_rate_limit

        if expect_success:
            assert resp.status_code == 302
            assert resp.url == '/'
        else:
            assert resp.status_code == 200

    invitations.invite('john', INVITATION_DURATION, create=True)
    device = _accept(client, models.Invitation.objects.get(), 'pw')
    client.logout()
    assert not _access_homepage(client)

    set_time(t0)
    # 3 failures and we should get locked out
    for _ in range(3):
        try_login(correct_otp=False, expect_limit=False, expect_success=False)

    # try some correct and incorrect logins, they should not work
    for _ in range(3):
        try_login(correct_otp=True, expect_limit=True, expect_success=False)
        try_login(correct_otp=False, expect_limit=True, expect_success=False)

    # one minute later, try again, it should work
    set_time(t0 + timedelta(minutes=1))
    try_login(correct_otp=True, expect_limit=False, expect_success=True)

    assert rate_limit_exceeded == [{'username': 'john'}] * 6
