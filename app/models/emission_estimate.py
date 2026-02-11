from sqlalchemy import Integer, Numeric, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base

class EmissionEstimate(Base):
    __tablename__ = "emission_estimates"

    estimate_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String)
    category_id: Mapped[str] = mapped_column(String)
    calculation_method: Mapped[str] = mapped_column(String)
    factor_id: Mapped[int] = mapped_column(Integer)
    estimated_co2e: Mapped[float] = mapped_column(Numeric)
    calculation_version: Mapped[str] = mapped_column(String)
    run_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
