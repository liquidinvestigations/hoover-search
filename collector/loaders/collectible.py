import re
import json
import yaml
import requests
from ..utils import open_url


class Url(object):

    def __init__(self, url):
        self.url = url

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

        msg = "failed to get text %s: %r" % (self.metadata['slug'], resp)
        raise RuntimeError(msg)


class Loader(object):

    def __init__(self, index, match='', **config):
        self.index = index
        self.match = match

    def documents(self):
        index_url = Url(self.index)
        with index_url.open() as i:
            index = yaml.safe_load(i)
            for doc in index['documents']:
                doc_url = index_url.join(doc)
                with doc_url.open() as d:
                    for line in d:
                        yield Document(line, doc_url)
