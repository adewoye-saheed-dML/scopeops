from datetime import datetime
from sqlalchemy.orm import Session
from app.models.spend import SpendRecord
from app.models.supplier import Supplier
from app.models.emission_factors import EmissionFactor
from decimal import Decimal, InvalidOperation
from app.models.category_factor_mapping import CategoryFactorMapping  # <--- Import this!

def calculate_emissions(db: Session):
    """
    Calculate CO2e for spend records.
    Priority:
        1. Supplier-level locked factor
        2. Existing manual factor on record
        3. Category-based factor (CategoryFactorMapping)
    """
    spend_records = db.query(SpendRecord).filter(
        SpendRecord.calculated_co2e == None
    ).all()

    updated = 0

    for record in spend_records:
        supplier = db.query(Supplier).filter(
            Supplier.id == record.supplier_id
        ).first()

        if not supplier:
            continue

        # ------------------------
        # Determine emission factor
        # ------------------------
        factor = None
        method = "Unknown"

        # Supplier-level factor (Highest Priority)
        if supplier.resolved_factor_id:
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.id == supplier.resolved_factor_id
            ).first()
            method = "Supplier_Locked"

        # Check if record already has a specific factor assigned manually
        if not factor and record.factor_used_id:
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.id == record.factor_used_id
            ).first()
            method = "Manual_Override"

        # Category Fallback 
        if not factor and record.category_code:
            mapping = db.query(CategoryFactorMapping).filter(
                CategoryFactorMapping.category_id == record.category_code,
                CategoryFactorMapping.is_active == True
            ).first()
            
            if mapping:
                factor = db.query(EmissionFactor).filter(
                    EmissionFactor.id == mapping.emission_factor_id
                ).first()
                method = "Category_Average"

        # If we still don't have a factor, we can't calculate
        if not factor:
            continue

        # ------------------------
        # Deterministic calculation
        # ------------------------
        try:
            spend_amount = Decimal(record.spend_amount)
            intensity = Decimal(factor.co2e_per_currency)
            
            record.calculated_co2e = spend_amount * intensity
            record.factor_used_id = factor.id
            record.calculated_at = datetime.utcnow()
            record.calculation_method = method
            
            updated += 1
        except (ValueError, TypeError, InvalidOperation):
           continue

    db.commit()
    return updated