import logging
import os
import typing as t
import string
import pathlib
import unidecode
import shutil
import re
import rdflib

from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, STORED, KEYWORD
from whoosh.analysis import CharsetFilter, StemmingAnalyzer, StopFilter
from whoosh.support.charset import accent_map
from whoosh.qparser import QueryParser, FuzzyTermPlugin
from whoosh.query import FuzzyTerm
from whoosh.scoring import TF_IDF, BM25F
from whoosh import scoring

from .lib_cfg import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())

WH_INDEX = False
DB_POOL = False


async def get_db():
    global DB_POOL  # pylint:disable=global-statement
    conn = await DB_POOL.acquire()
    try:
        yield conn
    finally:
        await DB_POOL.release(conn)


def words_get(raw_query: str) -> t.List[str]:

    if not raw_query:
        return []
    query = normalize(raw_query)
    return query.split()


def normalize(text: str, minimum_size=3) -> str:
    """
    Generic standaridzed text normalizing function
    Args:
        text: Unicode text to be normalized
        minimum_size: discard words below this size
    Returns:
        normalized text
    Examples:
        >>> normalize("le TexTe  Présenté")
        'texte presente'
    """
    # Remove punctuation
    table = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    text = text.translate(table)

    # Lowercase
    text = text.lower()

    # Remove short letter groups
    text = text.split()
    text = [t for t in text if len(t) >= minimum_size]
    text = ' '.join(text)

    # Accent folding
    text = unidecode.unidecode(text)
    return text


def init_state(force=False):
    index_dir = './indx'

    if check_table(index_dir) and not force and not config.key('force_recreate'):
        return open_dir(index_dir)

    # TODO: Build IDX
    # - get data
    # - write to whoosh
    #

    g = rdflib.Graph()

    query = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT *
WHERE {
    SERVICE <%s> {
        ?subject <http://www.w3.org/2004/02/skos/core#notation> ?term .
        ?subject <http://www.w3.org/2004/02/skos/core#prefLabel> ?plabel .
            OPTIONAL {
        ?subject <http://www.w3.org/2004/02/skos/core#altLabel> ?alabel
            FILTER (lang(?alabel) = 'fr')
          }
        FILTER (lang(?plabel) = 'fr')
    }
}

    # If testing
    # LIMIT 250
    """ % (config.key('sparql_endpoint'))
    logger.debug(query)
    qres = g.query(query)

    list = []
    i = 0
    for row in qres:
        i += 1
        list.append({
            'label': str(row.plabel),
            'url': str(row.subject),
            'tp': 'pref'
        })

        if row.alabel:
            list.append({
                'label': str(row.alabel),
                'url': str(row.subject),
                'tp': 'alt'
            })

    logger.info('Obtained %s terms, preparing to index' % i)
    create_table(index_dir, overwrite=True)

    idx = open_dir(index_dir)
    # Write to index
    with idx.writer() as w:
        for el in list:
            w.add_document(**el)

    logger.info('Indexes written, whoosh index ready')

    return idx


def check_table(index_dir: t.Union[str, pathlib.Path]) -> bool:
    """
    Vérifie l'existence des fichiers d'index Whoosh
    Args:
        index_dir: Directory supposée contenir l'index

    Returns:
        True si l'index Whoosh existe
    """
    index_dir = str(index_dir)
    return os.path.exists(index_dir) and exists_in(index_dir)


def create_table(index_dir, *, overwrite=False):
    # analyzer = StandardAnalyzer() | CharsetFilter(accent_map)
    analyzer = StemmingAnalyzer() | CharsetFilter(accent_map) | StopFilter(lang="fr")

    schema = Schema(
        label=TEXT(stored=True, analyzer=analyzer, lang='fr'),
        url=STORED,
        tp=STORED,
    )

    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    elif exists_in(index_dir):
        if not overwrite:
            logger.critical('An index already exists in %s; overwrite flag not set; abandonning', index_dir)
            raise RuntimeError('Index already exists')
        logger.warning('Index already found, deleting %s to start anew', index_dir)
        # FIXME: remove missing shutil
        shutil.rmtree(index_dir, ignore_errors=True, onerror=None)

        os.mkdir(index_dir)

    logger.info('Whoosh index %s ready for use', index_dir)
    create_in(index_dir, schema)
    return index_dir


class CustomFuzzyTerm(FuzzyTerm):
    def __init__(self, fieldname, text, boost=5.0, maxdist=2,  # pylint: disable=too-many-arguments
                 prefixlength=3, constantscore=False):
        super().__init__(fieldname, text, boost, maxdist, prefixlength, constantscore)


def match(query_str, idx, limit=40):
    ret_results = []

    query_words = words_get(query_str)
    if len(query_words) == 0:
        return ret_results

    with idx.searcher() as searcher:
        # Strict search, with forced correction
        parser = QueryParser('label', idx.schema)
        query = parser.parse(f'{query_str}')
        cor = searcher.correct_query(query, query_str)
        results = searcher.search(cor.query, limit=20)

        # Word-joker search
        parser = QueryParser('label', idx.schema)
        query = parser.parse(f'{query_str}*')
        results_partial = searcher.search(query, limit=20)
        results.upgrade_and_extend(results_partial)

        # Fuzzy search
        parser = QueryParser('label', idx.schema, termclass=CustomFuzzyTerm)
        parser.add_plugin(FuzzyTermPlugin())

        shortword = re.compile(r'\W*\b\w{1,3}\b')
        query_prep = shortword.sub('', query_str)
        query = parser.parse(query_prep)
        results_fuzzy = searcher.search(query, limit=limit)
        results.upgrade_and_extend(results_fuzzy)
        for res in results:
            print(res)
            ret_results.append({
                'uri': res['url'],
                'label': res['label'],
                'label_ln': 'fr',
                'label_type': res['tp'],
                'score': res.score
            })

    return sorted(ret_results, key=lambda e: e['score'], reverse=True)
