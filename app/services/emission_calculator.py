from datetime import datetime
from sqlalchemy.orm import Session
from app.models.spend import SpendRecord
from app.models.supplier import Supplier
from app.models.emission_factor import EmissionFactor


def calculate_emissions(db: Session):

    spend_records = db.query(SpendRecord).filter(
    SpendRecord.calculated_co2e == None
    ).all()

    updated = 0

    for record in spend_records:

        # Get supplier
        supplier = db.query(Supplier).filter(
            Supplier.supplier_id == record.supplier_id
        ).first()

        if not supplier:
            continue

        # Supplier must have locked factor
        if not supplier.resolved_factor_id:
            continue

        # Get emission factor
        factor = db.query(EmissionFactor).filter(
            EmissionFactor.id == supplier.resolved_factor_id
        ).first()

        if not factor:
            continue

        # Deterministic calculation
        record.calculated_co2e = float(record.spend_amount) * float(factor.co2e_per_currency)
        record.factor_used_id = factor.id
        record.calculated_at = datetime.utcnow()
        record.calculation_method = "Industry_IO_Locked"

        updated += 1

    db.commit()
    return updated
