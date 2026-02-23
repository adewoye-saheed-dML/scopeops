from datetime import datetime
from sqlalchemy.orm import Session
from app.models.spend import SpendRecord
from app.models.supplier import Supplier
from app.models.emission_factors import EmissionFactor
from decimal import Decimal, InvalidOperation
from app.models.category_factor_mapping import CategoryFactorMapping

def calculate_emissions(db: Session):
    """
    Calculate CO2e for spend/activity records.
    Priority:
        1. Supplier-level locked factor
        2. Existing manual factor on record
        3. Category-based factor (CategoryFactorMapping)
        
    NEW: Hybrid Calculation
        - If the factor is spend-based (USD), it multiplies by spend_amount.
        - If the factor is activity-based (kg, kWh), it multiplies by quantity.
    """
    # Fetch all records that haven't been calculated yet
    uncalculated_records = db.query(SpendRecord).filter(
        SpendRecord.calculated_co2e == None
    ).all()

    updated = 0

    for record in uncalculated_records:
        supplier = db.query(Supplier).filter(
            Supplier.id == record.supplier_id
        ).first()

        if not supplier:
            continue

        # Determine Emission Factor
    
        factor = None
        method = "Unknown"

        # Priority 1: Supplier-level factor
        if supplier.resolved_factor_id:
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.id == supplier.resolved_factor_id
            ).first()
            method = "Supplier_Locked"

        # Priority 2: Manual Override
        if not factor and record.factor_used_id:
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.id == record.factor_used_id
            ).first()
            method = "Manual_Override"

        # Priority 3: Category Fallback
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

        # If we still don't have a factor, we skip to the next record
        if not factor:
            continue

    
        # Hybrid Calculation Logic
    
        try:
            # Check the factor's unit to know if we need spend_amount or quantity
            is_spend_based = (factor.unit_of_measure.upper() == "USD")
            
            if is_spend_based and record.spend_amount is not None:
                base_value = Decimal(record.spend_amount)
            elif not is_spend_based and record.quantity is not None:
                base_value = Decimal(record.quantity)
            else:
                # Mismatch (e.g., factor needs 'kg' but user only gave 'spend_amount')
                # Skip calculation until the correct factor or data is provided
                continue

            # Calculate Total CO2e
            intensity = Decimal(factor.co2e_per_unit)
            record.calculated_co2e = base_value * intensity
            
            # Calculate Scope Breakdowns (If the factor provides them)
            if factor.scope_1_intensity is not None:
                record.calculated_scope_1 = base_value * Decimal(factor.scope_1_intensity)
            if factor.scope_2_intensity is not None:
                record.calculated_scope_2 = base_value * Decimal(factor.scope_2_intensity)
            if factor.scope_3_intensity is not None:
                record.calculated_scope_3 = base_value * Decimal(factor.scope_3_intensity)

            # Mark as calculated
            record.factor_used_id = factor.id
            record.calculated_at = datetime.utcnow()
            record.calculation_method = method
            
            updated += 1
            
        except (ValueError, TypeError, InvalidOperation):
           continue

    db.commit()
    return updated