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
        3. Category-based factor (CEDA Fallback & Direct Match)
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

        # Priority 3: Category Mapping or Direct CEDA Match
        if not factor and record.category_code:
            target_ext_id = None
            
            # 3a. Check if a custom mapping exists in the Resolution Center
            mapping = db.query(CategoryFactorMapping).filter(
                CategoryFactorMapping.category_id.ilike(record.category_code),
                CategoryFactorMapping.is_active == True
            ).first()

            if mapping:
                target_ext_id = mapping.emission_factor_id
            else:
                # 3b. Auto-Match: If no manual mapping exists, assume the category code IS a direct CEDA code
                clean_code = str(record.category_code).strip().upper()
                target_ext_id = f"OPEN-CEDA-2025-{clean_code}"

            # Now that we have the target ID, fetch the country multiplier
            if target_ext_id:
                # Try to match the exact region of the supplier
                if supplier.region:
                    factor = db.query(EmissionFactor).filter(
                        EmissionFactor.provider == "Open CEDA",
                        EmissionFactor.external_id == target_ext_id,
                        EmissionFactor.geography.ilike(supplier.region) 
                    ).first()
                    
                    if factor:
                        method = f"CEDA_{supplier.region}_Specific"

                # Fallback: Try 'Global' or 'US' if exact country match fails
                if not factor:
                    factor = db.query(EmissionFactor).filter(
                        EmissionFactor.provider == "Open CEDA",
                        EmissionFactor.external_id == target_ext_id,
                        EmissionFactor.geography.in_(["Global", "Rest of World", "RoW", "US"])
                    ).order_by(EmissionFactor.geography.desc()).first()
                    
                    if factor:
                        method = "CEDA_Global_Fallback"

        # Final Safety Check (Triggers Resolution Center)
        if not factor:
            record.calculated_co2e = None
            record.calculation_method = "Requires_Mapping"
            continue
            
        try:
            # Robust unit checking
            factor_unit = str(factor.unit_of_measure).upper()
            is_spend_based = any(u in factor_unit for u in ["USD", "$", "SPEND"])
            
            # Use Decimal for high-precision financial/carbon math
            if is_spend_based and record.spend_amount is not None:
                base_value = Decimal(str(record.spend_amount))
            elif not is_spend_based and record.quantity is not None:
                base_value = Decimal(str(record.quantity))
            else:
                val = record.spend_amount or record.quantity
                if val is not None:
                    base_value = Decimal(str(val))
                else:
                    continue

            # Calculate Total CO2e
            intensity = Decimal(str(factor.co2e_per_unit))
            record.calculated_co2e = base_value * intensity
            
            # Calculate Scope Breakdowns
            for scope in [1, 2, 3]:
                field_name = f'scope_{scope}_intensity'
                intensity_val = getattr(factor, field_name, None)
                if intensity_val is not None:
                    setattr(record, f'calculated_scope_{scope}', base_value * Decimal(str(intensity_val)))

            record.factor_used_id = factor.id
            record.calculated_at = datetime.utcnow()
            record.calculation_method = method
            
            updated += 1
            
        except (ValueError, TypeError, InvalidOperation) as e:
            print(f"Error calculating record {record.id}: {e}")
            continue

    db.commit()
    return updated