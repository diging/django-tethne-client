__all__ = ['Corpus', 'Paper', 'Author', 'Affiliation', 'Metadatum',
           'Identifier']


class BaseEntity(object):
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def __getitem__(self, key):
        return self.data.get(key, None)

    def __setitem__(self, key, value):
        raise RuntimeError('Whoa there! Result objects are immutable.')

    @property
    def id(self):
        return self['id']


class CorpusComponentMixin(object):
    @property
    def corpus(self):
        return self.client.follow_link(self['corpus'], Corpus, paginated=False)


class PaperComponentMixin(object):
    @property
    def paper(self):
        return self.client.follow_link(self['paper'], Paper, paginated=False)


class Corpus(BaseEntity):
    def __repr__(self):
        return u'Corpus: %s' % self.data.get('label', u'(no label)')

    @property
    def papers(self):
        return self.client.follow_link(self['papers'], Paper)

    @property
    def authors(self):
        return self.client.follow_link(self['authors'], Author)

    @property
    def metadata(self):
        return self.client.follow_link(self['metadata'], Metadatum)

    @property
    def affiliations(self):
        return self.client.follow_link(self['affiliations'], Affiliation)

    @property
    def institutions(self):
        return self.client.follow_link(self['institutions'], Institution)

    @property
    def citations(self):
        return self.client.follow_link(self['citations'], Paper)


class Paper(BaseEntity, CorpusComponentMixin):
    def __repr__(self):
        return u'Paper: %s' % self.data.get('title', u'(no title)')

    @property
    def authors(self):
        return self.client.follow_link(self['authors'], Author)

    @property
    def metadata(self):
        return self.client.follow_link(self['metadata'], Metadatum)

    @property
    def affiliations(self):
        return self.client.follow_link(self['affiliations'], Affiliation)

    @property
    def institutions(self):
        return self.client.follow_link(self['institutions'], Institution)

    @property
    def citations(self):
        return self.client.follow_link(self['citations'], Paper)

    @property
    def cited_by(self):
        return self.client.follow_link(self['cited_by'], Paper)


class Author(BaseEntity, CorpusComponentMixin, PaperComponentMixin):
    def __repr__(self):
        last_name = self.data.get('last_name', '(no last name)')
        first_name = self.data.get('first_name', '(no last name)')
        return u'Author: %s, %s' % (last_name, first_name)

    @property
    def affiliations(self):
        return self.client.follow_link(self['affiliations'], Affiliation)


class Affiliation(BaseEntity, CorpusComponentMixin, PaperComponentMixin):
    def __repr__(self):
        return u'Affiliation instance'

    @property
    def author(self):
        return self.client.follow_link(self['author'], Author)


class Metadatum(BaseEntity, CorpusComponentMixin, PaperComponentMixin):
    pass


class Identifier(BaseEntity, CorpusComponentMixin, PaperComponentMixin):
    pass
