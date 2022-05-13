from ..deps import (
    match,
    get_db,
)
from ..lib_cfg import config
from fastapi import APIRouter, Depends
from voc_api.models import (
    LinkResponse,
    LinkSet,
    User,
)
import logging
import urllib
import rdflib

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('DEBUG'))
logger.addHandler(logging.StreamHandler())


@router.get("/nav/{collection}", tags=["vocabulary"])
async def nav_collection(collection: str, db=Depends(get_db)):
    """
    Get root subjects of a collection
    """

    g = rdflib.Graph()
    query = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?label_fr ?subject
WHERE {
    SERVICE <%s> {
        ?subject <http://www.w3.org/2004/02/skos/core#prefLabel> ?label_fr .
        FILTER EXISTS {
         ?s <http://www.w3.org/2004/02/skos/core#hasTopConcept> ?subject
        }
        FILTER (lang(?label_fr) = 'fr')
    }
}
    """ % (config.key('sparql_endpoint'))
    logger.debug(query)
    qres = g.query(query)

    tree = []
    i = 0
    for row in qres:
        i += 1
        tree.append({
            'order': i,
            'labels': {'fr': str(row.label_fr)},
            'iri_self': str(row.subject),
            'iri_parent': None,
            'sub_documents_count': None,
        })
    logger.info('Obtained %s domains' % i)

    return {'tree': tree, 'documents': []}


@router.get("/nav/{collection}/{subject}", tags=['vocabulary'])
async def nav_collection(collection: str, subject: str, db=Depends(get_db)):
    """
    Get subject contents
    """
    # TODO : 
    # - Add related subjects
    # - Add alternate labels ?

    # ##################################################### Get Graph Subjects
    # ########################################################################
    g = rdflib.Graph()
    if '%' in subject:
        subject = urllib.parse.unquote(subject)

    query = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?label_fr ?subject ?label_parent_fr
WHERE {
    SERVICE <%s> {
        <%s> <http://www.w3.org/2004/02/skos/core#prefLabel> ?label_parent_fr .
        <%s> <http://www.w3.org/2004/02/skos/core#narrower> ?subject.
        ?subject <http://www.w3.org/2004/02/skos/core#prefLabel> ?label_fr .
        FILTER (lang(?label_fr) = 'fr')
        FILTER (lang(?label_parent_fr) = 'fr')
    }
}
    """ % (config.key('sparql_endpoint'), subject, subject)
    logger.debug(query)
    qres = g.query(query)

    parent_label = None
    tree = []
    i = 0
    for row in qres:
        i += 1
        if not parent_label:
            parent_label = {'fr': str(row.label_parent_fr)}
        tree.append({
            'order': i,
            'labels': {'fr': str(row.label_fr)},
            'iri': str(row.subject),
            'sub_documents_count': None,
        })

    # ##################################################### Get Database Links
    # ########################################################################
    sql = """
        SELECT term_iri
        FROM links
        WHERE term_iri = $1
        AND collection = $2
        ORDER BY date_created DESC
    """
    res = await db.fetch(sql, subject, collection)

    return {
        'parent': {'iri': subject, 'labels': parent_label},
        'tree': tree,
        'documents': [str(r['term_iri']) for r in res]
    }
