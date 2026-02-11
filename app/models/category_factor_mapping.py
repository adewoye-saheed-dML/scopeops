import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CategoryFactorMapping(Base):
    __tablename__ = "category_factor_mapping"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    category_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("categories.category_id"),
        nullable=False
    )

    emission_factor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emission_factors.id"),
        nullable=False
    )

    confidence: Mapped[str] = mapped_column(String, nullable=True)
    rationale: Mapped[str] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
