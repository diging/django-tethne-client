# django-tethne-client <a href="https://travis-ci.org/diging/django-tethne-client/builds"><img src="https://travis-ci.org/diging/django-tethne-client.svg" alt="build:"></a>

Python client for the django-tethne JSON API.

## Install

```shell
$ pip install -U django-tethne-client
```

## Examples

### Connect

```python
>>> from tethneweb.client import TethneClient
>>> client = TethneClient('http://tethne.web.instance.com', 'username', 'password')
```

### Get lists of things

```python
>>> corpora = client.list_corpora()
>>> corpora
[<tethneweb.classes.Corpus at 0x1042ac150>, <tethneweb.classes.Corpus at 0x1042ac105>]
```

### Get related things

```python
>>> corpus = corpora[0]
>>> corpus.papers[:]
[<tethneweb.classes.Paper at 0x104aa2e50>,
 <tethneweb.classes.Paper at 0x104aa2250>,
 <tethneweb.classes.Paper at 0x104aa2850>,
 <tethneweb.classes.Paper at 0x104aa2d10>,
 <tethneweb.classes.Paper at 0x104aa2310>,
 <tethneweb.classes.Paper at 0x104aa2510>,
 <tethneweb.classes.Paper at 0x104aa25d0>,
 <tethneweb.classes.Paper at 0x104aa24d0>,
 <tethneweb.classes.Paper at 0x104aa2110>,
 <tethneweb.classes.Paper at 0x104aa2b10>,
 <tethneweb.classes.Paper at 0x104aa2f90>,
 ...
 <tethneweb.classes.Paper at 0x104b80310>]
```

## Methods

### ``TethneClient``

#### List methods

* ``list_corpora(limit=100, **params)``: Returns a list of ``Corpus`` objects.
* ``list_papers(limit=100, **params)``: Returns a list of ``Paper`` objects.
* ``list_authors(limit=100, **params)``: Returns a list of ``Author`` objects.

All list methods take the following parameters:

* **``limit``** (default: 100): Maximum number of records to return.
* **``params``**: Additional keyword arguments are passed to the ``params`` argument when calling  [``requests.get()``](http://docs.python-requests.org/en/master/api/#requests.get).

#### Get methods

* ``get_corpus(id)``: Returns a ``Corpus`` object.
* ``get_paper(id)``: Returns a ``Paper`` object.
* ``get_author(id)``: Returns an ``Author`` object.
* ``get_institution(id)``: Returns an ``Institution`` object.

### ``Corpus``

### ``Paper``

### ``Author``

### ``Institution``

### ``Affiliation``

### ``Metadataum``

### ``Identifier``
