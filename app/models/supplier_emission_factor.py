from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from datetime import datetime
import uuid


class SupplierEmissionFactor(Base):
    __tablename__ = "supplier_emission_factors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id"),
        nullable=False
    )

    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)

    calculation_method: Mapped[str] = mapped_column(String, nullable=False)
    data_quality_tier: Mapped[str] = mapped_column(String, nullable=False)

    intensity_tco2e_per_usd: Mapped[float] = mapped_column(
        Numeric,
        nullable=False
    )

    source_disclosure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("supplier_disclosures.id"),
        nullable=True
    )

    industry_factor_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )

    locked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    supplier = relationship("Supplier", back_populates="emission_factors")
