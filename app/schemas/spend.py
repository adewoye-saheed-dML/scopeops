from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from decimal import Decimal

class SpendCreate(BaseModel):
    supplier_id: UUID
    category_code: str
    fiscal_year: int
    
   
    spend_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    
   
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    material_type: Optional[str] = None
    factor_used_id: Optional[UUID] = None

class SpendRead(SpendCreate):
    spend_id: int
    
    
    calculated_co2e: Optional[Decimal] = None
    calculated_scope_1: Optional[Decimal] = None
    calculated_scope_2: Optional[Decimal] = None
    calculated_scope_3: Optional[Decimal] = None
    
    factor_used_id: Optional[UUID] = None
    calculated_at: Optional[datetime] = None
    calculation_method: Optional[str] = None

    class Config:
        from_attributes = True