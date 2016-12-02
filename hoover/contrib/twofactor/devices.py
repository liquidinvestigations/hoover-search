import subprocess
from base64 import b32encode
from contextlib import contextmanager
from django_otp.plugins.otp_totp.models import TOTPDevice

APP_NAME = 'Hoover'

def create(user, username):
    return TOTPDevice.objects.create(
        user=user,
        name=username,
        confirmed=False,
    )

def get(user, id):
    return TOTPDevice.objects.devices_for_user(user).get(id=id)

def delete_all(user, keep=None):
    for old_device in TOTPDevice.objects.devices_for_user(user):
        if old_device == keep:
            continue
        old_device.delete()

def device_for_invitation(user, request):
    device_id = request.session.get('invitation_device_id')
    device = None
    if device_id:
        device = get(user, device_id)

    if not device:
        username = user.get_username()
        device = create(user, username)

    request.session['invitation_device_id'] = device.id

    return device

def setup_successful(user, device):
    delete_all(user, keep=device)

def qrencode(data):
    return subprocess.check_output(['qrencode', data, '-s', '5', '-o', '-'])

def qr_png(device, username):
    tpl = 'otpauth://totp/{app}:{username}?secret={secret}&issuer={app}'
    url = tpl.format(
        app=APP_NAME,
        username=username,
        secret=b32encode(device.bin_key).decode('utf8'),
    )
    return qrencode(url)
