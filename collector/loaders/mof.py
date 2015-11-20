import re
from ..utils import open_url


class MofLoader(object):

    class ParseError(RuntimeError):

        def __init__(self, filename):
            msg = "Can't parse filename %r" % filename
            RuntimeError.__init__(self, msg)

    def __init__(self, repo, match='', **config):
        self.repo = repo
        self.match = match

    def parse(self, filename):
        m = re.match(r'^mof(?P<part>\d)_(?P<year>\d{4})'
                     r'_(?P<number>\d+)\.pdf$', filename)
        if m is None:
            raise self.ParseError(filename)

        fields = {k: int(v) for k, v in m.groupdict().items()}
        filename_txt = filename.rstrip('.pdf') + '.txt'

        return {
            'url': self.repo + '/' + filename,
            'text_url': self.repo + '/' + filename_txt,
            'slug': "mof{part}-{year}-{number}".format(**fields),
            'title': "Monitorul Oficial partea {part}, {number}/{year}"
                .format(**fields),
        }

    def documents(self):
        for year in range(1990, 2016):
            with open_url(self.repo + '/%d.csv' % year) as f:
                for line in f:
                    filename = line.strip().split(',')[-1]

                    if self.match and not re.match(self.match, filename):
                        continue

                    try:
                        yield self.parse(filename)
                    except self.ParseError as e:
                        print e
