from datetime import datetime, timedelta
import pytest
from django.utils.timezone import utc, now
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from hoover.contrib.twofactor import invitations, models, devices

pytestmark = pytest.mark.django_db

@pytest.yield_fixture
def mock_time(monkeypatch):
    class mock_time:
        time = staticmethod(lambda: t.timestamp())
    t = now()
    patch = monkeypatch.setattr
    patch('hoover.contrib.twofactor.invitations.now', lambda: t)
    patch('hoover.contrib.twofactor.middleware.time', mock_time.time)
    patch('django_otp.plugins.otp_totp.models.time', mock_time)
    def set_time(value):
        nonlocal t
        assert t.tzinfo is utc
        t = value
    yield set_time

def _totp(device, now):
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits)
    totp.time = now.timestamp()
    return totp.token()

def _access_homepage(client):
    resp = client.get('/', follow=False)
    if resp.status_code == 200:
        assert '<input name="q"' in resp.content.decode('utf-8')
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
def test_flow(client, mock_time, minutes, username_ok, password_ok, code_ok,
        invitation, success):

    t0 = datetime(2016, 6, 13, 12, 0, 0, tzinfo=utc)
    t1 = t0 + timedelta(minutes=minutes)

    mock_time(t0)
    url = invitations.invite('john', create=True)
    assert not _access_homepage(client)

    mock_time(t1)
    client.get(url)

    if not invitation:
        assert TOTPDevice.objects.count() == 0
        return

    [device] = TOTPDevice.objects.all()
    hour = timedelta(hours=1)
    resp = client.post(url, {
        'username': 'john' if username_ok else 'ramirez',
        'password': 'secretz',
        'password-confirm': 'secretz' if password_ok else 'foobar',
        'code': _totp(device, t1) if code_ok else _totp(device, t1 + hour),
    })

    if success:
        assert "Verification successful." in resp.content.decode('utf-8')
        assert _access_homepage(client)

    else:
        assert not _access_homepage(client)

def _accept(invitation, password):
    from django.http import HttpRequest
    from django.contrib.sessions.backends.db import SessionStore
    request = HttpRequest()
    request.session = SessionStore()
    with devices.setup(invitation.user, None) as (device, setup_successful):
        invitations.accept(request, invitation, device, password)
        setup_successful()
    return device

@pytest.mark.parametrize('username,password,interval,success', [
    ('john', 'pw', timedelta(0), True),
    ('john', 'pw', timedelta(minutes=2), False),
    ('johnny', 'pw', timedelta(0), False),
    ('john', 'pwz', timedelta(0), False),
])
def test_login(client, username, password, interval, success):
    invitations.invite('john', create=True)
    device = _accept(models.Invitation.objects.get(), 'pw')
    assert not _access_homepage(client)
    client.post('/accounts/login/', {
        'username': username,
        'password': password,
        'otp_token': _totp(device, now() + interval),
    })
    assert _access_homepage(client) == success

def test_auto_logout(client, mock_time):
    t0 = datetime(2016, 6, 13, 12, 0, 0, tzinfo=utc)

    mock_time(t0)
    invitations.invite('john', create=True)
    device = _accept(models.Invitation.objects.get(), 'pw')
    assert not _access_homepage(client)
    client.post('/accounts/login/', {
        'username': 'john',
        'password': 'pw',
        'otp_token': _totp(device, t0),
    })
    assert _access_homepage(client)

    mock_time(t0 + timedelta(hours=2, minutes=59))
    assert _access_homepage(client)

    mock_time(t0 + timedelta(hours=3, minutes=0, seconds=5))
    assert not _access_homepage(client)
