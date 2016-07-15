__all__ = ['TethneClient',]

import json, requests
from urlparse import urlparse, parse_qs, urljoin, urlunparse, SplitResult
from urllib import urlencode

from tethneweb.classes import Corpus, Paper
from tethneweb.upload import CorpusHandler


class TethneClient(object):
    def __init__(self, endpoint, username, password, authenticate=True):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        if authenticate:
            self.authenticate()

    def _path(self, partial):
        return urljoin(self.endpoint, partial)

    def _auth_header(self):
        return {'Authorization': 'Token %s' % self.token}

    def _prep_path(self, path, params):
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

    def _handle_response(self, response, message=None):
        if response.status_code != requests.codes.ok:
            raise RuntimeError(message if message else 'Server returned status %i' % response.status_code)
        return response.json()

    def _get_or_fail(self, path, params={}, message=None):
        path = path if path.startswith('http') else self._path(path)
        path, params = self._prep_path(path, params)
        response = requests.get(path, params=params, headers=self._auth_header())
        return self._handle_response(response, message)

    def _post_or_fail(self, path, data, message=None, with_headers=False):
        response = requests.post(path if path.startswith('http') else self._path(path),
                                 data=data,
                                 headers=self._auth_header() if with_headers else {})
        return self._handle_response(response, message)

    def _get_paginated_list(self, path, limit=None, page_size=20, params={}):
        params.update({'limit': page_size})

        results = []
        current_page = path
        while current_page:
            data = self._get_or_fail(current_page, params=params)
            results += data.get('results')
            next_page = data.get('next', None)
            if next_page == current_page:
                raise RuntimeError('Infinite recursion conditions detected!')
            current_page = next_page

            if limit and len(results) >= limit:
                break
        return results

    def authenticate(self):
        """
        Attempt to retrieve an authentication token.
        """
        auth_data = {'username': self.username, 'password': self.password}
        message = 'Could not authenticate. Please check endpoint and ' \
                + ' credentials, and try again.'

        data = self._post_or_fail('api-token-auth/', auth_data, message)
        self.token = data.get('token', None)

    def follow_link(self, path, result_class, paginated=True, limit=None, **params):
        if paginated:
            results = self._get_paginated_list(path, limit=limit, params=params)
            return [result_class(self, result) for result in results]
        return result_class(self, self._get_or_fail(path, params=params))

    def list_corpora(self, limit=None, **params):
        """
        List all corpora to which the user has access.
        """
        results = self._get_paginated_list('rest/corpus/', limit=limit, params=params)
        return [Corpus(self, result) for result in results]

    def list_papers(self, limit=100, **params):
        """
        List all papers to which the user has access.
        """
        results = self._get_paginated_list('rest/paper/', limit=limit, params=params)
        return [Paper(self, result) for result in results]

    def list_authors(self, limit=100, **params):
        """
        List all papers to which the user has access.
        """
        results = self._get_paginated_list('rest/author_instance/', limit=limit, params=params)
        return [Author(self, result) for result in results]

    def list_institutions(self, limit=100, **params):
        """
        List all papers to which the user has access.
        """
        results = self._get_paginated_list('rest/institution_instance/', limit=limit, params=params)
        return [Institution(self, result) for result in results]

    def get_paper(self, id):
        return Paper(self._get_or_fail('rest/paper/%i/' % int(id)))

    def get_author(self, id):
        return Author(self._get_or_fail('rest/author_instance/%i/' % int(id)))

    def get_corpus(self, id):
        return Corpus(self._get_or_fail('rest/corpus/%i/' % int(id)))

    def get_institution(self, id):
        return Institution(self._get_or_fail('rest/institution_instance/%i/' % int(id)))

    def upload(self, tethne_corpus, label, source, batch_size=100):
        handler = CorpusHandler(self, tethne_corpus, label, source, batch_size)
        handler.run()

    def create_corpus(self, data):
        return Corpus(self, self._post_or_fail('rest/corpus/', data, with_headers=True))

    def create_bulk(self, model_name, data):
        return self._post_or_fail('rest/%s/' % model_name, {'data': json.dumps(data)}, with_headers=True)
