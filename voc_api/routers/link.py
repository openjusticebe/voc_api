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

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('DEBUG'))
logger.addHandler(logging.StreamHandler())


@router.get("/link", response_model=LinkResponse)
async def link_get(iri: str, db=Depends(get_db)):
    logger.debug('Get links for %s', iri)
    # Get term iri's associated with item iri's
    pass


@router.post("/link")
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
        op_uuid
    ) VALUES ( $1, $2, $3)
    RETURNING id_internal;
    """

    for term_iri in query.terms:
        relId = await db.fetchval(
            sql,
            query.item_iri,
            term_iri,
            op_uuid
        )

        logger.debug('Set (op %s / id %s) association %s -> %s', op_uuid, relId, query.item_iri, term_iri)

    return "ok"
