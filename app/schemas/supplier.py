from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class SupplierBase(BaseModel):
    supplier_id: str
    supplier_name: str
    strategic_flag: Optional[str] = None
    region: Optional[str] = None
    industry_name: Optional[str] = None  

class SupplierCreate(SupplierBase):
    pass

class SupplierRead(SupplierBase):
    resolved_factor_id: Optional[UUID] = None  
    factor_locked_at: Optional[datetime] = None 

    class Config:
        from_attributes = True
