from time import time
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.dispatch import receiver
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.signals import user_logged_in

LOGIN_TIME_SESSION_KEY = 'hoover.contrib.twofactor.login_time'

@receiver(user_logged_in)
def on_login_success(sender, request, **kwargs):
    request.session[LOGIN_TIME_SESSION_KEY] = time()

class AutoLogout:
    def process_request(self, request):
        if not settings.HOOVER_TWOFACTOR_AUTOLOGOUT:
            return
        user = request.user
        if user.is_authenticated():
            login_time = request.session.get(LOGIN_TIME_SESSION_KEY) or 0
            if time() - login_time > settings.HOOVER_TWOFACTOR_AUTOLOGOUT:
                logout(request)
                return HttpResponseRedirect(settings.HOOVER_BASE_URL)

class RequireAuth:
    def process_request(self, request):
        for prefix in ['/accounts/', '/invitation/']:
            if request.path.startswith(prefix):
                return

        user = request.user
        if user.is_verified():
            return

        resolved_login_url = resolve_url(settings.LOGIN_URL)
        return redirect_to_login(request.path, resolved_login_url, 'next')
