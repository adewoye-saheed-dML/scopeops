from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SupplierBase(BaseModel):
    supplier_name: str
    domain: Optional[str] = None
    industry_locked: str
    region: Optional[str] = None
    sbti_status: Optional[str] = None
    parent_id: Optional[UUID] = None

class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    id: UUID
    has_disclosure: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
