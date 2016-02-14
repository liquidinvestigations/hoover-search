import re
import json
import logging
import yaml
import requests
from ..utils import open_url

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Url(object):

    def __init__(self, url):
        self.url = url

    def __str__(self):
        return self.url

    def open(self):
        return open_url(self.url)

    def join(self, value):
        if re.match(r'^http[s]?://', value):
            return Url(value)

        else:
            return Url(self.url.rsplit('/', 1)[0] + '/' + value)


class Document(object):

    _NOT_PARSED = object()
    _parsed = _NOT_PARSED

    def __init__(self, raw, base_url):
        self._raw = raw
        self.base_url = base_url

    def _expand_urls(self, data):
        return dict(data,
            url=self.base_url.join(data['url']).url,
            text_url=self.base_url.join(data['text_url']).url,
        )

    @property
    def metadata(self):
        if self._parsed is Document._NOT_PARSED:
            self._parsed = self._expand_urls(json.loads(self._raw.decode('utf-8')))
        return self._parsed

    def text(self):
        resp = requests.get(self.metadata['text_url'])

        if resp.status_code == 200:
            return resp.text

        msg = "failed to get text %s: %r" % (self.metadata['id'], resp)
        raise RuntimeError(msg)


class Loader(object):

    label = "Collectible"

    def __init__(self, index, match='', **config):
        self.index = Url(index)
        self.match = match

    def get_metadata(self):
        logger.info("loading collection %s", self.index)
        with self.index.open() as i:
            return yaml.safe_load(i)

    def documents(self):
        for doc in self.get_metadata()['documents']:
            doc_url = self.index.join(doc)
            logger.info("loading document list %s", doc_url)
            with doc_url.open() as d:
                for line in d:
                    yield Document(line, doc_url)
