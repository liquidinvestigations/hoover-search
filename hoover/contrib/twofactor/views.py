from base64 import b64encode
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import render
from django_otp.forms import OTPAuthenticationForm
from . import devices
from . import invitations
from . import signals
from . import models

class AuthenticationForm(OTPAuthenticationForm):

    def clean_otp(self, user):
        try:
            return super().clean_otp(user)
        except ValidationError:
            signals.login_failure.send('hoover.contrib.twofactor',
                otp_failure=True)
            raise

@transaction.atomic
def invitation(request, code):
    invitation = invitations.get_or_404(code)
    success = False
    bad_token = None
    bad_username = False
    bad_password = False
    username = invitation.user.get_username()

    signals.invitation_open.send(models.Invitation, username=username)

    device = invitations.device_for_session(request, invitation)

    if request.method == 'POST':
        code = request.POST['code']
        if not device.verify_token(code):
            bad_token = True

        if request.POST['username'] != username:
            bad_username = True

        if request.POST['password'] != request.POST['password-confirm']:
            bad_password = True

        if not (bad_username or bad_password or bad_token):
            password = request.POST['password']
            invitations.accept(request, invitation, device, password)
            signals.invitation_accept.send(models.Invitation,
                username=username)
            success = True

    png_data = b64encode(devices.qr_png(device, username)).decode('utf8')
    otp_png = 'data:image/png;base64,' + png_data

    return render(request, 'totp-invitation.html', {
        'username': username,
        'otp_png': otp_png,
        'success': success,
        'bad_username': bad_username,
        'bad_password': bad_password,
        'bad_token': bad_token,
    })
