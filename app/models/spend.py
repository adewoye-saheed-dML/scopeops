from sqlalchemy import ForeignKey, Numeric, DateTime, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import uuid


class SpendRecord(Base):
    __tablename__ = "spend_records"

    spend_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )

    category_code: Mapped[str] = mapped_column(String, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)

   
    spend_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String, nullable=True)


    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String, nullable=True) # e.g., 'kg', 'kWh'
    material_type: Mapped[str] = mapped_column(String, nullable=True)   # e.g., 'Steel', 'Electricity'

   
    calculated_co2e: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=True)
    
    
    calculated_scope_1: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=True)
    calculated_scope_2: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=True)
    calculated_scope_3: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=True)

    factor_used_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emission_factors.id"), nullable=True
    )

    calculated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    calculation_method: Mapped[str] = mapped_column(String, nullable=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )