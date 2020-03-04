from ..contrib import installed


def default(request):
    return {
        'HOOVER_INSTALLED': installed,
    }
