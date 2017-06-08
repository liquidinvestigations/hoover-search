import json
from django.db import transaction
from . import es

def iter_collection(collection):
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

        def save_state():
            collection.crawl_state = json.dumps(state)
            collection.save()

        while state['stack']:
            doc_id = state['stack'].pop()
            doc = loader.get(doc_id)
            try:
                data = doc.get_data()
            except loader.DigestError:
                continue
            else:
                yield (doc, data)
            state['stack'].extend(child['id'] for child in data['children'])
            save_state()

        state = None
        save_state()


def crawl_collection(collection):
    for doc, data in iter_collection(collection):
        body = dict(data['content'], _hoover={'version': data['version']})
        es.index(collection.id, doc.doc_id, body)
