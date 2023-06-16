import time

from django.core.management.base import BaseCommand
from django.conf import settings

import requests

ES_ADDR = settings.HOOVER_ELASTICSEARCH_URL


def es_write_unlock():
    # https://github.com/liquidinvestigations/docs/wiki/Admin-Guide:-FAQ#elasticsearch-wont-index-documents--hypothesis-wont-save-annotations
    resp = requests.put(ES_ADDR + '/_cluster/settings', json={"persistent": {"cluster.blocks.read_only": False}})
    assert resp.ok and resp.json()['acknowledged'], 'cannot remove ES readonly mode from cluster settings'

    resp = requests.put(ES_ADDR + '/_all/_settings', json={"index.blocks.read_only_allow_delete": None})
    assert resp.ok and resp.json()['acknowledged'], 'cannot remove ES readonly mode from all index settings'


def check_es_write_unlocked():
    resp = requests.get(ES_ADDR + '/_cluster/settings').json()
    # elasticsearch has a funny way of encoding truth values...
    print(resp)
    assert 'false' == resp['persistent']['cluster']['blocks']['read_only'], 'ES cluster settings are read-only'


class Command(BaseCommand):
    help = "Unlock Elasticsearch write access and check if it's still locked."

    def handle(self, **options):
        es_write_unlock()
        # allow ES time to lock itself back up again
        time.sleep(0.5)
        check_es_write_unlocked()
        print('ES disk ok')
