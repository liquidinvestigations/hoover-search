import re
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

    def __init__(self, metadata):
        self.metadata = metadata

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
                    for item in yaml.safe_load_all(d):
                        if self.match:
                            if not re.search(self.match, item['slug']):
                                continue
                        item['url'] = doc_url.join(item['url']).url
                        item['text_url'] = doc_url.join(item['text_url']).url
                        yield Document(item)
