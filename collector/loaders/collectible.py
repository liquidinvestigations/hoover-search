import re
import yaml
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


class Loader(object):

    def __init__(self, index, match='', **config):
        self.index = index
        self.match = match

    def documents(self):
        index_url = Url(self.index)
        with index_url.open() as i:
            index = yaml.load(i)
            for doc in index['documents']:
                doc_url = index_url.join(doc)
                with doc_url.open() as d:
                    for item in yaml.load_all(d):
                        item['url'] = doc_url.join(item['url']).url
                        item['text_url'] = doc_url.join(item['text_url']).url
                        yield item
