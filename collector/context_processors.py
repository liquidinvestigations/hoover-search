from django.conf import settings

def default(request):
    return {
        'HOOVER_ASSETS': settings.HOOVER_ASSETS,
    }
