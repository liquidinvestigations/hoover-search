from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.conf import settings
import requests

PUBLIC_URL = settings.LIQUID_AUTH_PUBLIC_URL
INTERNAL_URL = settings.LIQUID_AUTH_INTERNAL_URL
CLIENT_ID = settings.LIQUID_AUTH_CLIENT_ID
CLIENT_SECRET = settings.LIQUID_AUTH_CLIENT_SECRET

class ClientError(Exception):
    pass

def oauth2_login(request):
    authorize_url = PUBLIC_URL + '/o/authorize/'
    return redirect(
        '{}?response_type=code&client_id={}'
        .format(authorize_url, CLIENT_ID)
    )

def oauth2_exchange(request):
    token_url = INTERNAL_URL + '/o/token/'
    redirect_uri = request.build_absolute_uri('/accounts/oauth2-exchange/')
    code = request.GET.get('code')
    data = {
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'code': code,
    }
    auth = (CLIENT_ID, CLIENT_SECRET)
    token_resp = requests.post(token_url, data=data, auth=auth)
    if token_resp.status_code != 200:
        raise ClientError(
            "Could not get token from {}: {!r}"
            .format(token_url, token_resp)
        )
    token_data = token_resp.json()
    access_token = token_data['access_token']
    token_type = token_data['token_type']
    if token_type != 'Bearer':
        raise ClientError(
            "Expected token_type='Bearer', got {!r}"
            .format(token_type)
        )
    refresh_token = token_data['refresh_token']
    profile_url = INTERNAL_URL + '/accounts/profile'
    profile_resp = requests.get(
        profile_url,
        headers={'Authorization': 'Bearer {}'.format(access_token)},
    )
    if profile_resp.status_code != 200:
        raise ClientError(
            "Could not get profile from {}: {!r}"
            .format(profile_url, profile_resp)
        )
    profile = profile_resp.json()
    user, created = User.objects.get_or_create(username=profile['login'])
    if created:
        user.save()

    is_admin = profile['is_admin']
    if is_admin != user.is_superuser or is_admin != user.is_staff:
        user.is_superuser = is_admin
        user.is_staff = is_admin
        user.save()

    login(request, user)

    return redirect(settings.LOGIN_REDIRECT_URL)

def oauth2_logout(request):
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)
