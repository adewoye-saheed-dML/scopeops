from sqlalchemy import String, Boolean, DateTime
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
    country: Mapped[str] = mapped_column(String, nullable=True)

    industry_locked: Mapped[str] = mapped_column(String, nullable=False)

    strategic_flag: Mapped[str] = mapped_column(String, nullable=True)
    region: Mapped[str] = mapped_column(String, nullable=True)

    sbti_status: Mapped[str] = mapped_column(String, nullable=True)
    has_disclosure: Mapped[bool] = mapped_column(Boolean, default=False)

    onboarding_method: Mapped[str] = mapped_column(
        String,
        default="manual"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    
    disclosures = relationship("SupplierDisclosure", back_populates="supplier")
    emission_factors = relationship("SupplierEmissionFactor", back_populates="supplier")
