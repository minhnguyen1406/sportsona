from pydantic import BaseModel
from typing import Optional


class CircuitResponse(BaseModel):
    circuit_id: str
    name: str
    locality: Optional[str] = None
    country: Optional[str] = None

    model_config = {"from_attributes": True}
