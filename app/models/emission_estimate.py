from sqlalchemy import Integer, Numeric, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
import uuid

class EmissionEstimate(Base):
    __tablename__ = "emission_estimates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id"),
        nullable=False
    )

    emission_factor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("supplier_emission_factors.id"),
        nullable=False
    )

    spend_usd: Mapped[float] = mapped_column(Numeric, nullable=False)

    estimated_co2e: Mapped[float] = mapped_column(Numeric, nullable=False)

    calculation_method: Mapped[str] = mapped_column(String, nullable=False)

    calculation_version: Mapped[str] = mapped_column(String, nullable=False)

    run_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
