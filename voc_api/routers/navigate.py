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
            'iri': str(row.subject),
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
    while '%' in subject:
        subject = urllib.parse.unquote(subject)

    query = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT *
WHERE {
    SERVICE <%s> {
        # current
        <%s> <http://www.w3.org/2004/02/skos/core#prefLabel> ?label_current_fr .

        FILTER (lang(?label_current_fr) = 'fr')

        OPTIONAL {
        <%s> <http://www.w3.org/2004/02/skos/core#narrower> ?subject.
        ?subject <http://www.w3.org/2004/02/skos/core#prefLabel> ?label_fr .
        FILTER (lang(?label_fr) = 'fr')
        }

        OPTIONAL {
        # parent
        <%s> <http://www.w3.org/2004/02/skos/core#broader> ?parent.
        ?parent <http://www.w3.org/2004/02/skos/core#prefLabel> ?label_parent_fr .
        FILTER (lang(?label_parent_fr) = 'fr')
        }

        OPTIONAL {
        # topconcept
        <%s> <http://www.w3.org/2004/02/skos/core#hasTopConcept> ?topConcept.
        ?topConcept <http://www.w3.org/2004/02/skos/core#prefLabel> ?label_topC_fr .

        FILTER (lang(?label_topC_fr) = 'fr')
        }

    }
}
    """ % (config.key('sparql_endpoint'), subject, subject, subject, subject)
    logger.debug(query)
    qres = g.query(query)

    current_label = None
    parent = None
    top = None
    tree = []
    i = 0
    for row in qres:
        i += 1
        if not current_label:
            current_label = {'fr': str(row.label_current_fr)}

        if not parent and row.parent:
            parent = {
                'iri': str(row.parent),
                'labels': {'fr': str(row.label_parent_fr)}
            }

        if not top and row.topConcept:
            top = {
                'iri': str(row.topConcept),
                'labels': {'fr': str(row.label_topC_fr)}
            }

        if row.label_fr:
            tree.append({
                'order': i,
                'labels': {'fr': str(row.label_fr)},
                'iri': str(row.subject),
                'sub_documents_count': None,
            })

    # ##################################################### Get Database Links
    # ########################################################################
    sql = """
        SELECT item_iri
        FROM links
        WHERE term_iri = $1
        AND collection = $2
        ORDER BY date_created DESC
    """
    res = await db.fetch(sql, subject, collection)

    return {
        'topConcept': top,
        'parent': parent,
        'current': {'iri': subject, 'labels': current_label},
        'tree': tree,
        'documents': [str(r['item_iri']) for r in res]
    }
