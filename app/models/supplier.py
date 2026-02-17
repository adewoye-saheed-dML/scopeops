# app/models/supplier.py

from sqlalchemy import String, Boolean, DateTime,Integer, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from datetime import datetime
import uuid


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    supplier_name: Mapped[str] = mapped_column(String, nullable=False)

    domain: Mapped[str] = mapped_column(String, nullable=True)

    industry_locked: Mapped[str] = mapped_column(String, nullable=False)

    region: Mapped[str] = mapped_column(String, nullable=True)

    sbti_status: Mapped[str] = mapped_column(String, nullable=True)

    has_disclosure: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    resolved_factor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emission_factors.id"),
        nullable=True
    )

    parent_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )

    parent = relationship(
        "Supplier",
        remote_side=[id],
        backref="children"
    )


    resolved_factor = relationship("EmissionFactor")
    disclosures = relationship("SupplierDisclosure", back_populates="supplier")

