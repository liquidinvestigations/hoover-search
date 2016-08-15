from django.conf import settings
from django.shortcuts import resolve_url
from django.contrib.auth.views import redirect_to_login

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
