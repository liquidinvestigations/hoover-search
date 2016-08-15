from django.conf import settings
import requests

def text(doc):
    resp = requests.put(
        settings.TIKA_URL + '/tika',
        headers={'Accept': 'text/plain'},
        data=doc,
    )
    return resp.content.decode('utf-8')

def html(doc):
    resp = requests.put(
        settings.TIKA_URL + '/tika',
        headers={'Accept': 'text/html'},
        data=doc,
    )
    return resp.content.decode('utf-8')
