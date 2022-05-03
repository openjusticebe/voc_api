from typing import List
from pydantic import BaseModel, AnyUrl, Field


class Suggestion(BaseModel):
    uri: AnyUrl
    label: str
    label_ln: str
    label_type: str
    score: float


class SuggestResponse(BaseModel):
    data: List[Suggestion] = Field([], description="Suggestion list")


class LinkResponse(BaseModel):
    data: List[str] = Field([], description="Associated terms")


class LinkSet(BaseModel):
    item_iri: str
    terms: List[str] = Field([], description="Terms to associate")
