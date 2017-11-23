from django.conf import settings
from django.shortcuts import render
from .invitations import invite


def create_invitations(modeladmin, request, queryset):
    username_list = [u.username for u in queryset]
    duration = settings.HOOVER_TWOFACTOR_INVITATION_VALID
    invitations = [
        (username, invite(username, duration, request.user))
        for username in username_list
    ]
    return render(request, 'admin-create-invitations.html', {
        'invitations': invitations,
    })


create_invitations.short_description = "Create invitations"
