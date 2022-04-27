from pydantic import BaseModel, AnyUrl


class SuggestResponse(BaseModel):
    uri: AnyUrl
    label: str
    label_ln: str
    label_type: str
