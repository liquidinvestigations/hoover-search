import json
from django.db import transaction
from . import es

def reset_crawl(collection):
    collection.crawl_state = 'null'
    collection.save()

def iter_collection(collection):
    while True:
        with transaction.atomic():
            collection = (
                type(collection).objects
                .select_for_update()
                .get(id=collection.id)
            )
            loader = collection.get_loader()
            state = json.loads(collection.crawl_state)

            if not state:
                state = {'stack': [loader.get_root_id()]}

            doc_id = state['stack'].pop()
            doc = loader.get(doc_id)

            try:
                data = doc.get_data()

            except loader.DigestError:
                pass

            else:
                yield (doc, data)
                state['stack'].extend(child['id'] for child in data['children'])

            if not state['stack']:
                state = None

            collection.crawl_state = json.dumps(state)
            collection.save()

            if not state:
                break


def crawl_collection(collection):
    for doc, data in iter_collection(collection):
        body = dict(data['content'], _hoover={'version': data['version']})
        es.index(collection.id, doc.doc_id, body)
