from pydantic import BaseModel
from typing import Optional
from uuid import UUID



class EmissionFactorCreate(BaseModel):
    provider: str
    name: str
    geography: str
    year: int
    co2e_per_currency: float
    version: str
    external_id: Optional[str] = None
    source_url: Optional[str] = None
    methodology: Optional[str] = None
