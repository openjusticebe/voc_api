from typing import List
from pydantic import BaseModel, AnyUrl, Field


class SuggestionList(BaseModel):
    uri: AnyUrl
    label: str
    label_ln: str
    label_type: str
    score: float


class SuggestResponse(BaseModel):
    data: List[SuggestionList] = Field([], description="Suggestion list")
