Hoover is a search tool for large collections of documents. It gues together
proven open-source technologies like elasticsearch and Apache Tika to aid the
work of investigative journalists.

**Documents are imported** from various sources: manual uploads, WebDAV
servers, like OwnCloud and Davros, datasets prepared in a special
metadata-rich ["collectible" format][collectible]. It's also possible to index
documents in elasticsearch separately and use this Django app only for search
and retrieval.

**Searching** is done through a user-friendly web interface that leverages
Lucene's rich query syntax. Hoover also provides an API to run queries using
the elasticsearch [query DSL][].

[collectible]: https://github.com/mgax/hoover/blob/master/docs/Collectible.md
[query dsl]: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html


## Installation

Hoover needs Python 3.4 or newer and a running elasticsearch server. You
probably want to set up a [virtualenv][] too.

[virtualenv]: http://docs.python-guide.org/en/latest/dev/virtualenvs/

1. Download the code, install dependencies

   ```shell
   git clone https://github.com/hoover/search.git
   cd hoover
   pipenv install
   ```

2. Copy and customize the configuration file

   ```shell
   cp hoover/site/settings/example_local.py hoover/site/settings/local.py
   ```

3. Prepare the database and create a Django user

   ```shell
   ./manage.py migrate
   ./manage.py createsuperuser
   ```

4. Download assets (jQuery and bootstrap) used by the default search UI and the
   two-factor login page. You can skip this step if you use the [advanced
   UI](https://github.com/hoover/ui) and don't enable two-factor login.

    ```shell
    ./manage.py downloadassets
    ./manage.py collectstatic
    ```

5. Run the server

   ```shell
   ./run devserver
   ```

6. Import a collection: first, create the collection in Django admin, at
   http://127.0.0.1:8000/admin/search/collection/. Then, click on "upload", and
   select a ZIP archive containing PDF files.

7. Run some search queries! There is a minimal search UI on the homepage of the
   Django site (http://127.0.0.1:8000/).


## Development

There is a test suite; run it with `./run testsuite`.


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
