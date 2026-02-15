from rapidfuzz import process
from sqlalchemy.orm import Session
from app.models.emission_factor import EmissionFactor
from app.models.supplier import Supplier
from datetime import datetime
from app.config.verified_suppliers import VERIFIED_SUPPLIERS
import uuid


def resolve_supplier_factor(db: Session, supplier: Supplier):
    """
    Assigns a resolved emission factor to a supplier.

    Priority:
    1. Use verified supplier disclosures if available.
    2. Fuzzy match the supplier's industry to DitchCarbon emission factors.
    """
    # Check for verified supplier overrides
    key = supplier.supplier_id.lower()
    if key in VERIFIED_SUPPLIERS:
        data = VERIFIED_SUPPLIERS[key]

        # Check if factor already exists in emission_factors
        factor = (
            db.query(EmissionFactor)
            .filter(
                EmissionFactor.name == data["name"],
                EmissionFactor.year == data["year"]
            )
            .first()
        )

        # If not, create a synthetic emission factor for this supplier
        if not factor:
            factor = EmissionFactor(
                id=uuid.uuid4(),
                external_id=None,
                provider="Verified Supplier Disclosure",
                name=data["name"],
                geography="Global",
                year=data["year"],
                co2e_per_currency=(data["scope_1"] + data["scope_2"] + data["scope_3"]) / data["revenue"],
                source_url=None,
                methodology="Direct corporate disclosure override",
                version="1.0",
            )
            db.add(factor)
            db.commit()
            db.refresh(factor)

        # Assign factor to supplier and lock timestamp
        supplier.resolved_factor_id = factor.id
        supplier.factor_locked_at = datetime.utcnow()
        db.commit()
        return factor

    # Fallback to fuzzy industry match if no verified supplier data
    if not supplier.industry_name:
        return None

    factors = db.query(EmissionFactor).all()
    factor_names = [f.name for f in factors]

    match = process.extractOne(
        supplier.industry_name,
        factor_names,
        score_cutoff=75
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
        supplier.factor_locked_at = datetime.utcnow()
        db.commit()

    return matched_factor
