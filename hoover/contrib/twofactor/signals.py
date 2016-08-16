from django.dispatch import Signal
from django.contrib.auth.signals import user_login_failed

invitation_open = Signal(['username'])
invitation_accept = Signal(['username'])
auto_logout = Signal(['username'])
login_failure = Signal(['otp_failure'])

def _on_login_failure(sender, **kwargs):
    login_failure.send('hoover.contrib.twofactor', otp_failure=False)

user_login_failed.connect(_on_login_failure)
