from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class SpendCreate(BaseModel):
    supplier_id: UUID
    category_code: str
    spend_amount: float
    currency: str
    fiscal_year: int


class SpendRead(SpendCreate):
    spend_id: int
    calculated_co2e: Optional[float] = None
    factor_used_id: Optional[UUID] = None
    calculated_at: Optional[datetime] = None
    calculation_method: Optional[str] = None

    class Config:
        from_attributes = True
