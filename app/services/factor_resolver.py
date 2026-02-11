from rapidfuzz import process
from sqlalchemy.orm import Session
from app.models.emission_factor import EmissionFactor
from app.models.supplier import Supplier


def resolve_supplier_factor(db: Session, supplier: Supplier):

    if not supplier.industry_name:
        return None

    # Get all industry names from emission_factors
    factors = db.query(EmissionFactor).all()
    factor_names = [f.name for f in factors]

    # Fuzzy match
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
        db.commit()

    return matched_factor
