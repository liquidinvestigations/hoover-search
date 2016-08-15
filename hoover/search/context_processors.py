from django.conf import settings
from ..contrib import installed

def default(request):
    return {
        'HOOVER_ASSETS': settings.HOOVER_ASSETS,
        'HOOVER_INSTALLED': installed,
    }
