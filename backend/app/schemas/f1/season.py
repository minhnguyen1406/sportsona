from pydantic import BaseModel


class SeasonResponse(BaseModel):
    year: int

    model_config = {"from_attributes": True}
