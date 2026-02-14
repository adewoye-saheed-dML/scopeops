from sqlalchemy import ForeignKey, Numeric, DateTime, String,Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import UUID as UUID_TYPE
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
    calculated_co2e: Mapped[float] = mapped_column(Numeric,nullable=True)
    factor_used_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emission_factors.id"),
        nullable=True
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    calculation_method: Mapped[str] = mapped_column(
        String,
        nullable=True
    )


