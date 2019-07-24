import qrcode
from base64 import b32encode
from contextlib import contextmanager
from django_otp.plugins.otp_totp.models import TOTPDevice

APP_NAME = 'Hoover'

def create(user):
    return TOTPDevice.objects.create(
        user=user,
        name=user.get_username(),
        confirmed=False,
    )

def get(user, id):
    return TOTPDevice.objects.devices_for_user(user).get(id=id)

def delete_all(user, keep=None):
    for old_device in TOTPDevice.objects.devices_for_user(user):
        if old_device == keep:
            continue
        old_device.delete()

def qr_png(device, username):
    tpl = 'otpauth://totp/{app}:{username}?secret={secret}&issuer={app}'
    url = tpl.format(
        app=APP_NAME,
        username=username,
        secret=b32encode(device.bin_key).decode('utf8'),
    )
    return bytes(qrcode.make(url))
