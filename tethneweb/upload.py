
import os
import cPickle as pickle
from collections import Counter, defaultdict
from uuid import uuid4



identifier_fields = ['doi', 'ayjid', 'issn', 'isbn', 'uri']
paper_fields = [
    ('date', 'publication_date'),
    ('title', 'title'),
    ('volume', 'volume'),
    ('issue', 'issue'),
    ('abstract', 'abstract'),
    ('journal', 'journal'),
]

exclude_fields = [
    'citations',
    'citedReferences'
]


class CorpusHandler(object):
    _add_order = [
        'paper',
        'identifier',
        'metadatum',
        'author_instance',
        'institution_instance',
        'affiliation_instance',
    ]

    def __init__(self, client, tethne_corpus, label, source, batch_size=100):
        self.client = client
        self.id_map = {}
        self.batch_size = batch_size
        self.hoppers = defaultdict(list)

        self.corpus = self.client.create_corpus({
            'source': source,
            'label': label,
        })
        self.tethne_corpus = tethne_corpus

    def run(self):
        for tethne_paper in self.tethne_corpus:
            paper_id = self._handle_paper(tethne_paper)

            for tethne_reference in getattr(tethne_paper, 'citedReferences', []):
                self._handle_cited_reference(tethne_reference, paper_id)

            if len(self.hoppers['paper']) >= self.batch_size:
                self._commit()
        self._commit()

    def _commit(self):
        for model_name in self._add_order:
            instances = []
            for datum in self.hoppers[model_name]:
                for field in ['paper_id', 'author_id', 'institution_id', 'cited_by_id']:
                    if field not in datum:
                        continue
                    ident = datum[field]
                    datum[field] = self.id_map.get(ident, ident)
                instances.append(datum)
            result = self.client.create_bulk(model_name, instances)
            self.id_map.update(result['id_map'])
            print 'Created %i instances of %s' % (len(self.hoppers[model_name]), model_name)
            self.hoppers[model_name] = []

    def _add_instance(self, model_name, instance):
        ident = str(uuid4())
        instance.update({'id': ident})
        self.hoppers[model_name].append(instance)
        return ident

    def _exclude_paper_field(self, field):
        exclude = list(zip(*paper_fields)[0]) + identifier_fields + exclude_fields
        return field.startswith('_') or field in exclude

    def _generate_metadata(self, tethne_paper):
        # Generate data for Metadatum model.
        metadata = []

        for field, value in tethne_paper.__dict__.iteritems():
            if self._exclude_paper_field(field):
                continue
            value = pickle.dumps(value)
            # if type(value) is not unicode:
            #     value = pickle.dumps(value)

            metadata.append({
                'name': field,
                'value': value,
                'corpus_id': self.corpus.id,

            })
        return metadata


    def _generate_identifiers(self, tethne_paper):
        # Generate data for Identifier model.
        identifiers = []
        for field in identifier_fields:
            value = getattr(tethne_paper, field, None)
            if value:
                identifiers.append({
                    'name': field,
                    'value': value,
                    'corpus_id': self.corpus.id,

                })
        return identifiers


    def _handle_paper(self, tethne_paper, **additional):
        paper_data = {}
        for pfield, dbfield in paper_fields:
            value = getattr(tethne_paper, pfield, None)
            if value:
                paper_data[dbfield] = value

        paper_data.update({
            'corpus_id': self.corpus.id,

        })
        paper_data.update(**additional)
        paper_id = self._add_instance('paper', paper_data)

        metadata = []
        for metadata_data in self._generate_metadata(tethne_paper):
            metadata_data.update({'paper_id': paper_id})
            self._add_instance('metadatum', metadata_data)

        identifiers = []
        for identifier_data in self._generate_identifiers(tethne_paper):

            identifier_data.update({'paper_id': paper_id})
            self._add_instance('identifier', identifier_data)

        self._handle_authors(tethne_paper, paper_id)
        return paper_id


    def _handle_cited_reference(self, tethne_reference, paper_id):
        return self._handle_paper(tethne_reference, cited_by_id=paper_id, concrete=False)


    def _handle_institution(self, address, paper_id):
        return self._add_instance('institution_instance', {
            'name': address[0],
            'country': address[1],
            'address': address[2],
            'paper_id': paper_id,
            'corpus_id': self.corpus.id,

        })

    def _handle_authors(self, tethne_paper, paper_id):
        # So that we don't create multiple InstitutionInstances for what are clearly
        #  the same institutions, we first extract all unique address tuples and
        #  create InstitutionInstances before proceeding.
        addresses = getattr(tethne_paper, 'addresses', {})
        normalize = lambda a: (a[0], a[1], ', '.join(a[2]))
        institution_instances = {i: self._handle_institution(i, paper_id) for i
                                 in set([normalize(j) for jset in addresses.values() for j in jset])}

        institutions = {
            name: [institution_instances[normalize(address)] for address in author_addresses]
            for name, author_addresses in addresses.items()
        }

        authors = []
        affiliations = []
        for tethne_author in tethne_paper.authors:
            author_id = self._add_instance('author_instance', {
                'paper_id': paper_id,
                'last_name': tethne_author[0][0],
                'first_name': tethne_author[0][1],
                'corpus_id': self.corpus.id,

            })

            tethne_affiliations = institutions.get(tethne_author,
                                                   institutions.get('__all__',
                                                                    None))
            if not tethne_affiliations:
                continue

            for institution_id in tethne_affiliations:
                self._add_instance('affiliation_instance', {
                    'paper_id': paper_id,
                    'author_id': author_id,
                    'institution_id': institution_id,
                    'confidence': 1./len(tethne_affiliations),
                    'corpus_id': self.corpus.id,
                })
