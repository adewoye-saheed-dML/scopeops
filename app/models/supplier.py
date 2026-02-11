# app/models/supplier.py

from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import uuid

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    supplier_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    strategic_flag: Mapped[str] = mapped_column(String, nullable=True)
    region: Mapped[str] = mapped_column(String, nullable=True)
    industry_name: Mapped[str] = mapped_column(String, nullable=True, index=True)
    sbti_status: Mapped[str] = mapped_column(String, nullable=True)
    has_disclosure: Mapped[bool] = mapped_column(nullable=True)

    resolved_factor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emission_factors.id"),
        nullable=True
    )