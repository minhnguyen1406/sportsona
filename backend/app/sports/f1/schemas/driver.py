from pydantic import BaseModel
from datetime import date
from typing import Optional


class DriverResponse(BaseModel):
    driver_id: str
    given_name: str
    family_name: str
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None

    model_config = {"from_attributes": True}
