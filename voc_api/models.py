from typing import List, Optional
from pydantic import BaseModel, AnyUrl, Field


class Suggestion(BaseModel):
    uri: AnyUrl
    label: str
    label_ln: str
    label_parent: str
    notation: str
    score: float


class SuggestResponse(BaseModel):
    data: List[Suggestion] = Field([], description="Suggestion list")


class LinkResponse(BaseModel):
    data: List[str] = Field([], description="Associated terms")


class LinkSet(BaseModel):
    item_iri: str
    terms: List[str] = Field([], description="Terms to associate")
    collection: str = Field(None, description="Add to collection")
    tags: List[str] = Field([], description="Tags to associate")


class User(BaseModel):
    email: str
    valid: Optional[bool] = True
    username: str
    admin: bool = True
