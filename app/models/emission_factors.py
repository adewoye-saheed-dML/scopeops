# app/models/emission_factor.py

import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    # Internal primary key (never external)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # External reference (DitchCarbon, USEEIO, etc.)
    external_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)

    # Factor metadata
    name: Mapped[str] = mapped_column(String, nullable=False)
    geography: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Core emission intensity
    co2e_per_currency: Mapped[float] = mapped_column(Numeric, nullable=False)

    # Audit metadata
    source_url: Mapped[str] = mapped_column(String, nullable=True)
    methodology: Mapped[str] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
