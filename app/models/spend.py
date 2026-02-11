from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SpendRecord(Base):
    __tablename__ = "spend_records"

    spend_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String)
    category_code: Mapped[str] = mapped_column(String)
    spend_amount: Mapped[float] = mapped_column(Numeric)
    currency: Mapped[str] = mapped_column(String)
    fiscal_year: Mapped[int] = mapped_column(Integer)

