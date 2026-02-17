from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from datetime import datetime
import uuid


class SupplierDisclosure(Base):
    __tablename__ = "supplier_disclosures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False
    )

    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)

    revenue_usd: Mapped[float] = mapped_column(Numeric, nullable=False)

    scope_1_tco2e: Mapped[float] = mapped_column(Numeric, nullable=True)
    scope_2_market_tco2e: Mapped[float] = mapped_column(Numeric, nullable=True)
    scope_2_location_tco2e: Mapped[float] = mapped_column(Numeric, nullable=True)

    scope_3_total_tco2e: Mapped[float] = mapped_column(Numeric, nullable=True)

    assurance_level: Mapped[str] = mapped_column(String, nullable=True)

    source_url: Mapped[str] = mapped_column(String, nullable=True)

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    supplier = relationship("Supplier", back_populates="disclosures")
