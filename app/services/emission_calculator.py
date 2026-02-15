from datetime import datetime
from sqlalchemy.orm import Session
from app.models.spend import SpendRecord
from app.models.supplier import Supplier
from app.models.emission_factor import EmissionFactor

def calculate_emissions(db: Session):
    """
    Calculate CO2e for spend records.
    Priority:
        1. Supplier-level locked factor
        2. Fallback to spend-based / industry factor if supplier factor not available
    """
    spend_records = db.query(SpendRecord).filter(
        SpendRecord.calculated_co2e == None
    ).all()

    updated = 0

    for record in spend_records:
        supplier = db.query(Supplier).filter(
            Supplier.supplier_id == record.supplier_id
        ).first()

        if not supplier:
            continue

        # ------------------------
        # Determine emission factor
        # ------------------------
        factor = None

        # Supplier-level factor
        if supplier.resolved_factor_id:
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.id == supplier.resolved_factor_id
            ).first()

        # Fallback: spend-based / industry factor
        if not factor:
            # If spend record already has a factor, use it
            if record.factor_used_id:
                factor = db.query(EmissionFactor).filter(
                    EmissionFactor.id == record.factor_used_id
                ).first()
            # Otherwise, skip calculation
            else:
                continue

        if not factor:
            continue

        # ------------------------
        # Deterministic calculation
        # ------------------------
        record.calculated_co2e = float(record.spend_amount) * float(factor.co2e_per_currency)
        record.factor_used_id = factor.id
        record.calculated_at = datetime.utcnow()

        # Track which calculation method was applied
        if supplier.resolved_factor_id:
            record.calculation_method = "Supplier_Locked"
        else:
            record.calculation_method = "Spend_Fallback"

        updated += 1

    db.commit()
    return updated
