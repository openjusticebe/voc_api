from ..deps import (
    match,
    get_db,
)
from ..auth import (
    get_current_active_user_opt,
    credentials_exception,
)
from fastapi import APIRouter, Depends
from voc_api.models import (
    LinkResponse,
    LinkSet,
    User,
)
from starlette.requests import Request
import logging
import uuid
import asyncpg

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('DEBUG'))
logger.addHandler(logging.StreamHandler())


@router.get("/link", response_model=LinkResponse, tags=["vocabulary"])
async def link_get(iri: str, collection: str = None, db=Depends(get_db)):
    logger.debug('Get links for %s', iri)

    if collection:
        sql = """
        SELECT term_iri
        FROM links
        WHERE item_iri = $1
        AND collection = $2
        ORDER BY date_created DESC
        """
        res = await db.fetch(sql, iri, collection)

    else:
        sql = """
        SELECT term_iri
        FROM links
        WHERE item_iri = $1
        AND collection IS NULL
        ORDER BY date_created DESC
        """
        res = await db.fetch(sql, iri)

    return {'data': [str(r['term_iri']) for r in res]}


@router.post("/link", tags=["vocabulary"])
async def link_set(
        query: LinkSet,
        request: Request,
        current_user: User = Depends(get_current_active_user_opt),
        db=Depends(get_db)):
    # Set term-item association
    if not current_user or not current_user.valid:
        raise credentials_exception

    op_uuid = uuid.uuid4()

    sql = """
    INSERT INTO links (
        item_iri,
        term_iri,
        tags,
        collection,
        op_uuid,
        ukey
    ) VALUES ( $1, $2, $3, $4, $5, $6)
    RETURNING id_internal;
    """

    for term_iri in query.terms:
        try:
            relId = await db.fetchval(
                sql,
                query.item_iri,
                term_iri,
                query.tags,
                query.collection,
                op_uuid,
                current_user.email
            )

            logger.debug('Set (op %s / id %s) association %s -> %s', op_uuid, relId, query.item_iri, term_iri)
        except asyncpg.exceptions.UniqueViolationError:
            logger.warn('Association already exists: %s -> %s', query.item_iri, term_iri)

    return "ok"
