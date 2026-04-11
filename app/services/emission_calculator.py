from datetime import datetime
from sqlalchemy.orm import Session
from app.models.spend import SpendRecord
from app.models.supplier import Supplier
from app.models.emission_factors import EmissionFactor
from decimal import Decimal, InvalidOperation
from app.models.category_factor_mapping import CategoryFactorMapping
from app.services.tree_rollup import get_effective_factor


def calculate_emissions(db: Session):
    """
    Calculate CO2e for spend/activity records.
    Priority:
        1. Corporate Tree / Supplier-level factor
        2. Existing manual factor on record
        3. Category-based factor (CEDA Fallback)
    """
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

        factor = None
        method = "Unknown"

        # Priority 1: Corporate Tree Cascade
        tree_factor = get_effective_factor(db, supplier.id)
        if tree_factor:
            factor = tree_factor
            # Let's smartly label it so users know if it cascaded or was direct
            if supplier.resolved_factor_id == factor.id:
                method = "Supplier_Locked"
            else:
                method = "Corporate_Tree_Cascade"

        # Priority 2: Manual Override
        if not factor and record.factor_used_id:
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.id == record.factor_used_id
            ).first()
            if factor:
                method = "Manual_Override"

        # Priority 3: Category Fallback (CEDA)
        if not factor and record.category_code:
            mapping = db.query(CategoryFactorMapping).filter(
                CategoryFactorMapping.category_id.ilike(record.category_code),
                CategoryFactorMapping.is_active == True
            ).first()

            # Fixed indentation here so it only runs if a mapping is found
            if mapping:
                factor = db.query(EmissionFactor).filter(
                    EmissionFactor.provider == "Open CEDA",
                    EmissionFactor.external_id == mapping.emission_factor_id,
                    EmissionFactor.geography == supplier.region  # Fixed to use .region instead of .country
                ).first()
                    
                if factor:
                    method = "CEDA_Region_Specific"
                else:
                    # US/Global Fallback
                    factor = db.query(EmissionFactor).filter(
                        EmissionFactor.provider == "Open CEDA",
                        EmissionFactor.external_id == mapping.emission_factor_id,
                        EmissionFactor.geography == "US"
                    ).first()
                    if factor:
                        method = "CEDA_Regional_Fallback"

        # Final Safety Check
        if not factor:
            record.calculated_co2e = None
            record.calculation_method = "Requires_Mapping"
            continue
            
        try:
            # Robust unit checking
            factor_unit = str(factor.unit_of_measure).upper()
            is_spend_based = ("USD" in factor_unit or "$" in factor_unit or "SPEND" in factor_unit)
            
            if is_spend_based and record.spend_amount is not None:
                base_value = Decimal(record.spend_amount)
            elif not is_spend_based and record.quantity is not None:
                base_value = Decimal(record.quantity)
            else:
                # Fallback: if it's spend based but they provided quantity, or vice versa, 
                if record.spend_amount is not None:
                    base_value = Decimal(record.spend_amount)
                elif record.quantity is not None:
                    base_value = Decimal(record.quantity)
                else:
                    continue

            # Calculate Total CO2e
            intensity = Decimal(factor.co2e_per_unit)
            record.calculated_co2e = base_value * intensity
            
            # Calculate Scope Breakdowns (Using getattr to safely handle schema variations)
            if getattr(factor, 'scope_1_intensity', None) is not None:
                record.calculated_scope_1 = base_value * Decimal(factor.scope_1_intensity)
            if getattr(factor, 'scope_2_intensity', None) is not None:
                record.calculated_scope_2 = base_value * Decimal(factor.scope_2_intensity)
            if getattr(factor, 'scope_3_intensity', None) is not None:
                record.calculated_scope_3 = base_value * Decimal(factor.scope_3_intensity)

            record.factor_used_id = factor.id
            record.calculated_at = datetime.utcnow()
            record.calculation_method = method
            
            updated += 1
            
        except (ValueError, TypeError, InvalidOperation) as e:
            print(f"Error calculating record {record.id}: {e}")
            continue

    db.commit()
    return updated