from pydantic import BaseModel

class SpendCreate(BaseModel):
    supplier_id: str
    category_code: str
    spend_amount: float
    currency: str
    fiscal_year: int

class SpendRead(SpendCreate):
    spend_id: int

    class Config:
        from_attributes = True
