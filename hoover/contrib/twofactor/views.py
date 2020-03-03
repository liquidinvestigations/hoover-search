from base64 import b64encode
from django.conf import settings
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import render
from django_otp.forms import OTPAuthenticationForm
from . import devices
from . import invitations
from . import signals
from . import models

if settings.HOOVER_TWOFACTOR_RATELIMIT:
    from hoover.contrib.ratelimit.limit import RateLimit

    (_l, _i) = settings.HOOVER_TWOFACTOR_RATELIMIT
    _login_limit = RateLimit(_l, _i)

    def rate_limit(username):
        key = 'hoover.contrib.twofactor:' + username
        return _login_limit.access(key)

else:
    def rate_limit(username):
        return False


class AuthenticationForm(OTPAuthenticationForm):

    def clean_otp(self, user):
        if user:
            username = user.get_username()
            if rate_limit(username):
                signals.rate_limit_exceeded.send(
                    'hoover.contrib.twofactor',
                    username=username,
                )
                raise ValidationError("Your account is temporarily locked "
                                      "because of too many login failures. Please try again "
                                      "in a few minutes.", code='ratelimit')

        try:
            return super().clean_otp(user)
        except ValidationError as e:
            signals.login_failure.send('hoover.contrib.twofactor',
                                       otp_failure=True)
            raise


@transaction.atomic
def invitation(request, code):
    invitation = invitations.get_or_404(code)
    bad_token = None
    bad_username = False
    bad_password = False
    username = invitation.user.get_username()

    signals.invitation_open.send(models.Invitation, username=username)

    device = invitations.device_for_session(request, invitation)

    if request.method == 'POST':
        if not device.verify_token(request.POST['code']):
            bad_token = True

        if request.POST['username'] != username:
            bad_username = True

        password = request.POST['password']
        if password != request.POST['password-confirm']:
            bad_password = True

        if not (bad_username or bad_password or bad_token):
            invitations.accept(request, invitation, device, password)
            signals.invitation_accept.send(models.Invitation,
                                           username=username)

            return render(request, 'totp-invitation-success.html')

    png_data = b64encode(devices.qr_png(device, username)).decode('utf8')
    otp_png = 'data:image/png;base64,' + png_data

    return render(request, 'totp-invitation-form.html', {
        'username': username,
        'otp_png': otp_png,
        'bad_username': bad_username,
        'bad_password': bad_password,
        'bad_token': bad_token,
    })
