import unittest, json, sys, mock
sys.path.append('.')
from tethneweb.client import TethneClient, Request
from tethneweb.classes import *
from tethneweb.results import Result, ResultList
from urlparse import urlparse, parse_qs, urljoin

import random


class MockResponse:
    def __init__(self, status_code, content, as_json=True):
        self.status_code = status_code
        self.content = content
        self.as_json = as_json

    def json(self):
        if self.as_json:
            return json.loads(self.content)
        return self.content


def _new_mocked_client():
    post = mock.Mock(side_effect=mock_requests_post)
    get = mock.Mock(side_effect=mock_requests_get)
    client = TethneClient('http://e.com', 'u', 'p', post_method=post, get_method=get)
    return client, get, post


def _new_mocked_request(path, retries=3):
    post = mock.Mock(side_effect=mock_requests_post)
    get = mock.Mock(side_effect=mock_requests_get)
    client = mock.Mock()
    request = Request(client, path, params={}, headers={}, get_method=get,
                      post_method=post, retries=retries)

    return request, get, post


def ok(fpath):
    with open(fpath, 'rb') as f:
        return f.read()


class mock_id_map(dict):
    def __getitem__(self, key):
        return random.randint(0, 5000)


def mock_requests_post(path, data={}, headers={}):
    try:
        o = urlparse(path)
        data.update(parse_qs(o.query))
    except Exception as E:
        return MockResponse(400, 'bad bad bad')

    code = 200

    if o.path.endswith('api-token-auth/'):
        if all([
                'username' in data,
                'password' in data,
                data['username'],
                data['password']
            ]):
            return MockResponse(200, '{"token" : "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}')
        return MockResponse(400, "bad bad bad")
    elif o.path.endswith('corpus/'):
        content = ok('tests/responses/corpus.json')

    else:
        return MockResponse(200, {'id_map': mock_id_map()}, as_json=False)
    return MockResponse(code, content)


def mock_requests_get(path, params={}, headers={}):
    try:
        o = urlparse(path)
        params.update(parse_qs(o.query))
    except:
        return MockResponse(400, 'bad bad bad')

    code = 200
    content = None
    if o.path.endswith('corpus/'):
        content = ok('tests/responses/corpus-list.json')
    elif o.path.endswith('paper_instance/'):
        if params.get('corpus', None) == '1':
            if params.get('offset', None) == '180':
                content = ok('tests/responses/paper-list-for-corpus-last.json')
            else:
                content = ok('tests/responses/paper-list-for-corpus.json')
        else:
            content = ok('tests/responses/paper-list.json')
    elif o.path.endswith('paper_instance/1/'):
        content = ok('tests/responses/paper-detail.json')
    elif o.path.endswith('author_instance/'):
        if params.get('paper', None) == '1':
            content = ok('tests/responses/authorinstance-list-for-paper.json')
        else:
            content = ok('tests/responses/authorinstance-list.json')
    elif o.path.endswith('affiliation_instance/'):
        if params.get('author', None) == '1':
            content = ok('tests/responses/affiliationinstance-list-for-author.json')
    else:
        code, content = 400, 'never heard of it'

    if code == 200 and 'Authorization' not in headers:
        return MockResponse(200, '[]')
    return MockResponse(code, content)


class TestAuthentication(unittest.TestCase):
    def test_authenticate(self, *args):
        post = mock.Mock(side_effect=mock_requests_post)
        self.client = TethneClient('http://end.com', 'user', 'pass', authenticate=False, post_method=post)
        self.client.authenticate()
        self.assertTrue(hasattr(self.client, 'token'))
        self.assertTrue(self.client.token is not None)
        self.assertEqual(post.call_count, 1)


class TestRetries(unittest.TestCase):
    def test_bad_route(self):
        request, get, post = _new_mocked_request('bad/path/indeed')
        request.get()
        self.assertEqual(get.call_count, 3)



class TestCreate(unittest.TestCase):
    def test_create_corpus(self):
        client, get, post = _new_mocked_client()

        corpus = client.create_corpus({'label': 'test', 'source': 'WOS'})
        self.assertIsInstance(corpus, Corpus)
        self.assertIsInstance(corpus.id, int)

        # Once for auth, and then again for create.
        self.assertEqual(post.call_count, 2)

    def test_create_bulk(self):
        client, get, post = _new_mocked_client()
        self.assertEqual(post.call_count, 1)
        client.create_bulk('paper_instance', [{'title': 'bob'}])
        self.assertEqual(post.call_count, 2)
        client.create_bulk('paper_instance', [{'title': 'bob'}])
        self.assertEqual(post.call_count, 3)

    def test_upload(self):
        from tethne.readers import wos
        tethne_corpus = wos.read('tests/data/wos.txt')

        client, get, post = _new_mocked_client()
        client.upload(tethne_corpus, 'a test', 'WOS', 1000)
        # Authorization, corpus creation, and then six models.
        self.assertEqual(post.call_count, 8)

    def test_upload_alt(self):
        """
        This Corpus is big, and has special characters in it.
        """
        from tethne.readers import wos
        tethne_corpus = wos.read('tests/data/1-500.txt')

        client, get, post = _new_mocked_client()
        client.upload(tethne_corpus, 'a test', 'WOS', 5000)
        # Authorization, corpus creation, and then six models.
        self.assertEqual(post.call_count, 44)


class TestGet(unittest.TestCase):
    def test_slice(self):
        client, get, post = _new_mocked_client()

        corpora = client.list_corpora()
        self.assertEqual(get.call_count, 0, 'should not GET until __getitem__')

        self.assertIsInstance(corpora, ResultList)
        self.assertIsInstance(corpora[0:5], list)
        self.assertEqual(get.call_count, 1, 'did not GET after __getitem__ ')

        corpus = corpora[0]
        papers = corpus.papers
        self.assertEqual(get.call_count, 2)

        self.assertIsInstance(papers[5:20], list)
        self.assertEqual(get.call_count, 3)

        self.assertIsInstance(papers[5:40], list)
        self.assertEqual(get.call_count, 5)

        self.assertIsInstance(papers[:], list)
        self.assertEqual(get.call_count, 15)

        self.assertIsInstance(papers[:5], list)
        self.assertEqual(get.call_count, 16)

        self.assertIsInstance(papers[:10:2], list)
        self.assertEqual(get.call_count, 21)


    def test_corpora(self):
        client, get, post = _new_mocked_client()

        corpora = client.list_corpora()
        self.assertEqual(get.call_count, 0, 'should not GET until __getitem__')

        self.assertIsInstance(corpora, ResultList)
        self.assertIsInstance(corpora[0], Corpus)
        self.assertEqual(get.call_count, 1, 'did not GET after __getitem__ ')

    def test_corpus_papers(self):
        client, get, post = _new_mocked_client()

        corpora = client.list_corpora()
        self.assertEqual(get.call_count, 0, 'should not GET until __getitem__')

        papers = corpora[0].papers
        self.assertEqual(get.call_count, 1, 'should only GET for the Corpus')

        self.assertIsInstance(papers, ResultList)
        self.assertIsInstance(papers[0], Paper)
        self.assertEqual(get.call_count, 2, 'did not GET again for the Paper')


    def test_paper_authors(self):
        client, get, post = _new_mocked_client()

        papers = client.list_papers()
        self.assertEqual(get.call_count, 0, 'should not GET until __getitem__')

        authors = papers[0].authors
        self.assertEqual(get.call_count, 1, 'should only GET for the Corpus')

        self.assertIsInstance(authors, ResultList)
        self.assertIsInstance(authors[0], Author)
        self.assertEqual(get.call_count, 2, 'did not GET again for the Author')

    def test_author_paper(self):
        client, get, post = _new_mocked_client()

        papers = client.list_papers()
        self.assertEqual(get.call_count, 0, 'should not GET until __getitem__')

        paper = papers[0]
        authors = paper.authors
        self.assertEqual(get.call_count, 1, 'should only GET for the Paper')

        author = authors[0]
        self.assertEqual(get.call_count, 2, 'did not GET for the Author')

        paper = author.paper
        self.assertEqual(get.call_count, 3, 'did not GET for the Paper')
        self.assertIsInstance(paper, Paper)

        self.assertEqual(paper.id, papers[0].id)
        self.assertEqual(get.call_count, 3, 'should not GET again for same key')

    def test_author_affiliations(self):
        client, get, post = _new_mocked_client()

        papers = client.list_papers()
        authors = papers[0].authors
        affiliations = authors[0].affiliations
        self.assertIsInstance(affiliations, ResultList)
        self.assertIsInstance(affiliations[0], Affiliation)
        self.assertEqual(get.call_count, 3)


    def test_papers(self):
        client, get, post = _new_mocked_client()

        papers = client.list_papers()
        self.assertIsInstance(papers, ResultList)
        self.assertIsInstance(papers[0], Paper)
        self.assertEqual(get.call_count, 1)


if __name__ == '__main__':
    unittest.main()
