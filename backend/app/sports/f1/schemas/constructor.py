from pydantic import BaseModel
from typing import Optional


class ConstructorResponse(BaseModel):
    constructor_id: str
    name: str
    nationality: Optional[str] = None

    model_config = {"from_attributes": True}
