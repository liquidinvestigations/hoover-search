Hoover is a search tool for large collections of documents. It glues together
proven open-source technologies like elasticsearch and Apache Tika to aid the
work of investigative journalists.


**Searching** is done through a user-friendly web interface that leverages
Lucene's rich query syntax. Hoover also provides an API to run queries using
the elasticsearch [query DSL][].

[query dsl]: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html


## Installation

Use [Liquid Investigations](https://github.com/liquidinvestigations/docs/wiki)


## Development

There is a test suite; run it with `./run testsuite` on the
`hoover-search` container.


## Running in production

[Waitress](http://docs.pylonsproject.org/projects/waitress/) is installed as
part of the dependencies. It's a production-quality threaded wsgi server. Pick
a port number, say 8888, and run it like this - it doesn't daemonize so you can
start it from supervisor or another modern daemon manager:

```shell
./run server --host=127.0.0.1 --port=8888
```

Then you probably want to set up a reverse proxy in front of the app. Here's
the minimal nginx config:

```nginx
location / {
  proxy_pass http://localhost:8888;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Configuration

To customize hoover's behaviour you can set the following Django settings in
`hoover/site/settings/local.py`:

* `HOOVER_HYPOTHESIS_EMBED_URL`: The URL to embed the Hypothesis client, e.g.
  `https://hypothes.is/embed.js`


## Snoop and external collections

For a large dataset, it's not practical to upload files through the admin UI,
so you can use [hoover-snoop](https://github.com/hoover/snoop). It's a tool for
pre-processing a collection, extracting metadata from emails and documents, and
accessing the contents of archives and email attachments. Snoop comes as a
standalone Django app, it listens on an HTTP port where it serves document
previews and raw documents, and it handles indexing of documents in
elasticsearch by itself.

To use it with *hoover-search*, first set up the snoop service, analyze the
data, send it to elasticsearch, then go back to *hoover-snoop* and create a new
collection of type *External* with the following options:

```json
{
  "documents": "http://localhost:8001/doc",
  "renderDocument": true
}
```

The `documents` URL is composed of the URL of *hoover-snoop*
(`http://localhost:8001` in this example) followed by `/doc`.

`renderDocument` tells *hoover-search* to use the new `doc.html` view from
*hoover-ui* to render the document preview pages. If you're not using
*hoover-ui* then omit this flag.
