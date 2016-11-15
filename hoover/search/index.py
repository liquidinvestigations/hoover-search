import logging
import json
from django.db import transaction
from . import es

logger = logging.getLogger(__name__)


class TextMissing(RuntimeError):
    pass


def index(collection, doc):
    data = doc.get_data()
    index_doc = dict(
        data.get('content'),
        _version=data['version'],
    )
    es.index(collection.id, index_doc)
    logger.debug('%s ok', doc.id)


def update_collection(collection):
    logger.info('updating %r', collection)
    loader = collection.get_loader()

    state = json.loads(collection.loader_state)
    if state:
        print('resuming load:', state)
        feed_state = state['feed_state']
        report = state['report']
        resume = True

    else:
        feed_state = None
        report = {}
        resume = False

    def save_state(new_state):
        collection.loader_state = json.dumps(new_state)
        collection.save()

    def count(key):
        report[key] = report.get(key, 0) + 1

    while True:
        logger.debug('page %s', feed_state)
        (page, feed_state) = loader.feed_page(feed_state)

        if resume:
            resume = False
            es_versions = {}
        else:
            doc_id_list = [doc['id'] for doc in page]
            es_versions = es.versions(collection.id, doc_id_list)

        for doc in page:
            assert doc['version'] is not None
            if es_versions.get(doc['id']) == doc['version']:
                logger.info('reached known document %r %r, stopping',
                    doc['id'], doc['version'])
                feed_state = None
                break

            body = dict(doc['content'], _hoover={'version': doc['version']})
            es.index(collection.id, doc['id'], body)
            logger.debug('%s indexed', doc['id'])
            count('indexed')

        if not feed_state:
            break

        save_state({'feed_state': feed_state, 'report': report})
        print(report)

    save_state(None)
    print(report)
