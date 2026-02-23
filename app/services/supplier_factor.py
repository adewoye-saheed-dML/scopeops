from rapidfuzz import process
from sqlalchemy.orm import Session
from app.models.emission_factors import EmissionFactor
from app.models.supplier import Supplier
from datetime import datetime
from app.config.verified_suppliers import VERIFIED_SUPPLIERS
import uuid

def resolve_supplier_factor(db: Session, supplier: Supplier):
    """
    Assigns a resolved emission factor to a supplier.

    Priority:
    1. Use verified supplier disclosures if available.
    2. Fuzzy match the supplier's industry to available emission factors.
    """
    
    # Check for Verified Supplier Overrides
    match_key = None

    if supplier.domain:
        domain_key = supplier.domain.lower().strip()
        if domain_key in VERIFIED_SUPPLIERS:
            match_key = domain_key

    if not match_key and supplier.supplier_name:
        name_key = supplier.supplier_name.lower().strip()
        if name_key in VERIFIED_SUPPLIERS:
            match_key = name_key
    
    if match_key:
        data = VERIFIED_SUPPLIERS[match_key]

        factor = db.query(EmissionFactor).filter(
            EmissionFactor.name == data["name"],
            EmissionFactor.year == data["year"]
        ).first()

        # If not, create a synthetic emission factor for this supplier
        if not factor:
            # Calculate total and granular intensities
            revenue = float(data["revenue"])
            total_emissions = float(data["scope_1"] + data["scope_2"] + data["scope_3"])
            
            factor = EmissionFactor(
                id=uuid.uuid4(),
                external_id=None,
                provider="Verified Supplier Disclosure",
                name=data["name"],
                # ---Geographic Hierarchy Fallback ---
                geography=supplier.region if supplier.region else "Global",
                year=data["year"],
                # --- Hybrid and Granular Scope Data ---
                unit_of_measure="USD",
                co2e_per_unit=(total_emissions / revenue),
                scope_1_intensity=(float(data["scope_1"]) / revenue),
                scope_2_intensity=(float(data["scope_2"]) / revenue),
                scope_3_intensity=(float(data["scope_3"]) / revenue),
                source_url=None,
                methodology="Direct corporate disclosure override",
                version="1.0",
                owner_id=supplier.owner_id  
            )
            db.add(factor)
            db.commit()
            db.refresh(factor)

        supplier.resolved_factor_id = factor.id
        db.commit()
        return factor


    # 2. Fallback to Fuzzy Industry Match
    if not supplier.industry_locked:
        return None

    factors = db.query(EmissionFactor).all()
    factor_names = [f.name for f in factors]

    match = process.extractOne(
        supplier.industry_locked,
        factor_names,
        score_cutoff=90
    )

    if not match:
        return None

    matched_name = match[0]
    matched_factor = (
        db.query(EmissionFactor)
        .filter(EmissionFactor.name == matched_name)
        .order_by(EmissionFactor.year.desc())
        .first()
    )

    if matched_factor:
        supplier.resolved_factor_id = matched_factor.id
        db.commit()

    return matched_factor