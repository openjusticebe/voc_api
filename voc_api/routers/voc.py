from ..deps import match
from fastapi import APIRouter, Depends
from voc_api.models import (
    SuggestResponse
)

router = APIRouter()


@router.get("/suggest/{begin}", response_model=SuggestResponse, tags=["crud"])
async def labels(begin: str, lang: str):
    """
    Return matching word labels (only search from beginning of string)
    """

    # TODO:
    # Use whoosh match result

    # Test payload
    payload = {
        'uri': 'http://example.com/uri',
        'label': 'somelabel',
        'label_ln': 'fr',
        'label_type': 'pref',
    }

    return payload
