from pydantic import BaseModel


class SuggestionOut(BaseModel):
    kind: str
    id: str
    label: str
    sublabel: str
    href: str
