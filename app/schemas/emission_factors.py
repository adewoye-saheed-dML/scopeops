from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class EmissionFactorBase(BaseModel):
    provider: str
    name: str
    geography: str
    year: int
    

    unit_of_measure: str = "USD"
    co2e_per_unit: float
    scope_1_intensity: Optional[float] = None
    scope_2_intensity: Optional[float] = None
    scope_3_intensity: Optional[float] = None

    
    version: str
    external_id: Optional[str] = None
    source_url: Optional[str] = None
    methodology: Optional[str] = None

class EmissionFactorCreate(EmissionFactorBase):
    pass

class EmissionFactorRead(EmissionFactorBase):
    id: UUID

    class Config:
        from_attributes = True