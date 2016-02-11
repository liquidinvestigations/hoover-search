# Collectible

`collectible` is a data format that hoover can easily import. It consists of an
index file and one or more lists of documents.


### index file

```yaml
title: "My fair collection"
documents:
  - foo.yaml
  - http://example.com/bar.yaml
```

This is the main file describing the collection. `documents` is a list of URLs,
relative or absolute, to document lists.


### document list

```yaml
---
{"id": "one", "title": "One", "url": "one.pdf", "text_url": "one.txt"}
---
id: "two"
title: "Two"
url: "http://example.com/two.pdf"
text_url: "http://example.com/two.txt"
```

A list of documents. Each document is represented by a yaml document that
contains the following fields. Yaml documents use `---` as separator. Don't add
a final `---` because it will generate a final blank document. You can use a
JSON library to generate yaml because any JSON document is a valid yaml
document.

* `id` - unique identifier of the document.
* `title` - document title, presented to the user in the search results list.
* `url` - link to the main representation of the document; this will be
  presented to the user when they click on the search result.
* `text_url` - link to a text-only representation of the document; this will be
  indexed.
