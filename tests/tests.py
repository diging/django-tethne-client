import unittest, json, sys, mock
sys.path.append('.')
from tethneweb.client import TethneClient
from tethneweb.classes import *
from urlparse import urlparse, parse_qs, urljoin


class MockResponse:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content

    def json(self):
        return json.loads(self.content)


def mock_requests_authenticate(endpoint, data={}, headers={}):
    if all([
            endpoint,
            'username' in data,
            'password' in data,
            data['username'],
            data['password']
        ]):
        return MockResponse(200, '{"token" : "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}')
    return MockResponse(400, "bad bad bad")


def ok(fpath):
    with open(fpath, 'rb') as f:
        return f.read()

def mock_requests_get(path, params={}, headers={}):
    try:
        o = urlparse(path)
        params.update(parse_qs(o.query))
    except:
        return MockResponse(400, 'bad bad bad')

    if 'Authorization' not in headers:
        return MockResponse(200, '[]')

    code = 200
    if o.path.endswith('corpus/'):
        content = ok('tests/responses/corpus-list.json')
    elif o.path.endswith('paper/'):
        if params.get('corpus', None) == '1':
            if params.get('offset', None) == '180':
                content = ok('tests/responses/paper-list-for-corpus-last.json')
            else:
                content = ok('tests/responses/paper-list-for-corpus.json')
        else:
            content = ok('tests/responses/paper-list.json')
    elif o.path.endswith('paper/1/'):
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
    return MockResponse(code, content)


class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.client = TethneClient('http://end.com', 'user', 'pass', authenticate=False)

    @mock.patch('requests.post', new=mock_requests_authenticate)
    def test_authenticate(self, *args):
        self.client.authenticate()
        self.assertTrue(hasattr(self.client, 'token'))
        self.assertTrue(self.client.token is not None)


class TestGet(unittest.TestCase):
    @mock.patch('requests.post', new=mock_requests_authenticate)
    @mock.patch('requests.get', new=mock_requests_get)
    def test_corpora(self, *args):
        self.client = TethneClient('http://end.com', 'user', 'pass')
        corpora = self.client.list_corpora()
        self.assertIsInstance(corpora, list)
        self.assertIsInstance(corpora[0], Corpus)

    @mock.patch('requests.post', new=mock_requests_authenticate)
    @mock.patch('requests.get', new=mock_requests_get)
    def test_corpus_papers(self, *args):
        self.client = TethneClient('http://end.com', 'user', 'pass')
        corpora = self.client.list_corpora()
        papers = corpora[0].papers
        self.assertIsInstance(papers, list)
        self.assertIsInstance(papers[0], Paper)

    @mock.patch('requests.post', new=mock_requests_authenticate)
    @mock.patch('requests.get', new=mock_requests_get)
    def test_paper_authors(self, *args):
        self.client = TethneClient('http://end.com', 'user', 'pass')
        papers = self.client.list_papers()
        authors = papers[0].authors
        self.assertIsInstance(authors, list)
        self.assertIsInstance(authors[0], Author)

    @mock.patch('requests.post', new=mock_requests_authenticate)
    @mock.patch('requests.get', new=mock_requests_get)
    def test_author_paper(self, *args):
        self.client = TethneClient('http://end.com', 'user', 'pass')
        papers = self.client.list_papers()
        authors = papers[0].authors
        paper = authors[0].paper
        self.assertIsInstance(paper, Paper)
        self.assertEqual(paper.id, papers[0].id)

    @mock.patch('requests.post', new=mock_requests_authenticate)
    @mock.patch('requests.get', new=mock_requests_get)
    def test_author_affiliations(self, *args):
        self.client = TethneClient('http://end.com', 'user', 'pass')
        papers = self.client.list_papers()
        authors = papers[0].authors
        affiliations = authors[0].affiliations
        self.assertIsInstance(affiliations, list)
        self.assertIsInstance(affiliations[0], Affiliation)

    @mock.patch('requests.post', new=mock_requests_authenticate)
    @mock.patch('requests.get', new=mock_requests_get)
    def test_papers(self, *args):
        self.client = TethneClient('http://end.com', 'user', 'pass')
        papers = self.client.list_papers()
        self.assertIsInstance(papers, list)
        self.assertIsInstance(papers[0], Paper)


if __name__ == '__main__':
    unittest.main()
