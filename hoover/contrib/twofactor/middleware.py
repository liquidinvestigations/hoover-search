from time import time
import re
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.dispatch import receiver
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.signals import user_logged_in
from . import signals

LOGIN_TIME_SESSION_KEY = 'hoover.contrib.twofactor.login_time'


@receiver(user_logged_in)
def on_login_success(sender, request, **kwargs):
    request.session[LOGIN_TIME_SESSION_KEY] = time()


class AutoLogout(MiddlewareMixin):

    def process_request(self, request):
        if not settings.HOOVER_TWOFACTOR_AUTOLOGOUT:
            return

        user = request.user
        if user.is_authenticated:
            login_time = request.session.get(LOGIN_TIME_SESSION_KEY) or 0
            if time() - login_time > settings.HOOVER_TWOFACTOR_AUTOLOGOUT:
                signals.auto_logout.send(AutoLogout,
                    username=user.get_username())
                logout(request)
                login = "{}?next={}".format(settings.LOGIN_URL, request.path)
                return HttpResponseRedirect(login)


class RequireAuth(MiddlewareMixin):

    def process_request(self, request):
        WHITELIST = [
            r'^/accounts/',
            r'^/invitation/',
            r'^/static/',
            r'^/_ping$',
            r'^/_is_staff$',
        ]
        for pattern in WHITELIST:
            if re.match(pattern, request.path):
                return

        user = request.user
        if user.is_verified():
            return

        resolved_login_url = resolve_url(settings.LOGIN_URL)
        return redirect_to_login(request.path, resolved_login_url, 'next')
