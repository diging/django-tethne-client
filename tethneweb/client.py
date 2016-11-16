__all__ = ['TethneClient',]

import json, requests, copy, jsonpickle, time
from urlparse import urlparse, parse_qs, urljoin, urlunparse, SplitResult
from urllib import urlencode

from tethneweb.classes import Corpus, Paper
from tethneweb.upload import CorpusHandler
from tethneweb.results import Result, ResultList


class Request(object):
    def __init__(self, client, url, params={}, headers={},
                 get_method=requests.get, post_method=requests.post,
                 retries=3):
        self.url, self.params = self._prep_path(url, params)
        self.headers = headers
        self.client = client
        self.get_method = get_method
        self.post_method = post_method
        self.retries_start = retries
        self.retries = retries

    def set_header(self, key, value):
        self.headers.update({key: value})

    def set_param(self, key, value):
        self.params.update({key: value})

    def _handle_response(self, response):
        if response.status_code != requests.codes.ok:
            raise IOError(response.status_code)
        return response.json()

    def _prep_path(self, path, params={}):
        """
        Pull query parameters from ``path`` and update ``params``.

        Returns
        -------
        tuple
            (url, params)

        """
        o = urlparse(path)
        params.update({k: v[0] for k, v in parse_qs(o.query).iteritems()})
        new = SplitResult(o.scheme, o.netloc, o.path, '', '')
        return new.geturl(), params

    def clone(self):
        return Request(self.client, self.url, params=copy.copy(self.params),
                       headers=copy.copy(self.headers),
                       get_method=self.get_method,
                       post_method=self.post_method,
                       retries=self.retries_start)

    def get(self):
        while self.retries > 0:
            response = self.get_method(self.url, params=self.params, headers=self.headers)
            try:
                return self._handle_response(response)
            except IOError:
                self.retries -= 1
                time.sleep(1)


    def post(self):
        while self.retries > 0:
            response = self.post_method(self.url, data=self.params, headers=self.headers)
            try:
                return self._handle_response(response)
            except IOError:
                self.retries -= 1
                time.sleep(1)



class TethneClient(object):
    def __init__(self, endpoint, username, password, authenticate=True,
                 get_method=requests.get, post_method=requests.post):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.get_method = get_method
        self.post_method = post_method
        if authenticate:
            self.authenticate()

    def _methods(self):
        return {'get_method': self.get_method, 'post_method': self.post_method}

    def _path(self, partial):
        return u'/'.join([self.endpoint, partial])
        # return urljoin(self.endpoint, partial)

    def _auth_header(self):
        return {'Authorization': 'Token %s' % self.token}

    def _new_request(self, *args, **kwargs):
        kwargs.update(self._methods())
        return Request(self, *args, **kwargs)

    def _get_or_fail(self, path, params={}, message=None):
        path = path if path.startswith('http') else self._path(path)
        return self._new_request(path, params, self._auth_header())

    def _post_or_fail(self, path, data, with_headers=False):
        path = path if path.startswith('http') else self._path(path)
        headers = self._auth_header() if with_headers else {}
        return self._new_request(path, data, headers)

    def authenticate(self):
        """
        Attempt to retrieve an authentication token.
        """
        auth_data = {'username': self.username, 'password': self.password}
        message = 'Could not authenticate. Please check endpoint and ' \
                + ' credentials, and try again.'

        data = self._post_or_fail('api-token-auth/', auth_data).post()
        self.token = data.get('token', None)

    def follow_link(self, path, result_class=dict, paginated=True, limit=None, **params):
        request = self._new_request(path, params, self._auth_header())
        if paginated:
            return ResultList(request, result_class)
        return Result(request, result_class)

    def list_corpora(self, **params):
        """
        List all corpora to which the user has access.
        """
        return ResultList(self._get_or_fail('rest/corpus/', params=params), Corpus)

    def list_papers(self, **params):
        """
        List all papers to which the user has access.
        """
        return ResultList(self._get_or_fail('rest/paper_instance/', params=params), Paper)

    def list_authors(self, **params):
        """
        List all papers to which the user has access.
        """
        return ResultList(self._get_or_fail('rest/author_instance/', params=params), Author)

    def list_institutions(self, **params):
        """
        List all papers to which the user has access.
        """
        return ResultList(self._get_or_fail('rest/institution_instance/', params=params), Institution)

    def check_unique(self, checksum, collection_id):
        params = {
            'checksum': checksum,
            'collection': collection_id,
        }
        request = self._get_or_fail('rest/check_unique/', params=params)
        response = request.get()
        return response.get('result') == 'true'

    def get_paper(self, id):
        return Result(self._get_or_fail('rest/paper_instance/%i/' % int(id)), Paper)

    def get_author(self, id):
        return Result(self._get_or_fail('rest/author_instance/%i/' % int(id)), Author)

    def get_corpus(self, id):
        return Result(self._get_or_fail('rest/corpus/%i/' % int(id)), Corpus)

    def get_institution(self, id):
        return Result(self._get_or_fail('rest/institution_instance/%i/' % int(id)), Institution)

    def upload(self, tethne_corpus, label, source, batch_size=100, corpus=None, skip_duplicates=True):
        handler = CorpusHandler(self, tethne_corpus, label, source, batch_size, corpus=corpus, skip_duplicates=skip_duplicates)
        handler.run()

    def create_corpus(self, data):
        return Corpus(self, self._post_or_fail('rest/corpus/', data, with_headers=True).post())

    def create_bulk(self, model_name, data):
        return self._post_or_fail('rest/%s/' % model_name, {'data': jsonpickle.encode(data)}, with_headers=True).post()
