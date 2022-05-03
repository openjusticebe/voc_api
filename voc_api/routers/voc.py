from ..deps import match
from fastapi import APIRouter
from voc_api.models import (
    SuggestResponse
)
import voc_api.deps as deps
from voc_api.deps import match, logger

router = APIRouter()


@router.get("/suggest/{begin}", response_model=SuggestResponse, tags=["crud"])
async def labels(begin: str, lang: str):
    """
    Return matching word labels (only search from beginning of string)
    """

    # TODO:
    # Use whoosh match result
    logger.debug("query: %s" % begin)
    list = match(begin, deps.WH_INDEX)

    return {
        'data': list
    }
