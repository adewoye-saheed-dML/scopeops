from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.database import get_db
from app.models.supplier import Supplier
from app.models.emission_factor import EmissionFactor
from app.schemas.supplier import SupplierCreate, SupplierRead
from rapidfuzz import process

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

# -----------------------
# Utility: Resolve Factor
# -----------------------
def resolve_supplier_factor(db: Session, supplier: Supplier):
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

# -----------------------
# POST: Create Supplier
# -----------------------
@router.post("/", response_model=SupplierRead)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    try:
        supplier = Supplier(**payload.dict())
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        # Resolve emission factor after creation
        resolve_supplier_factor(db, supplier)

        db.refresh(supplier)
        return supplier

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Supplier already exists."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Internal Server Error: {str(e)}"
        )

# -----------------------
# GET: List Suppliers
# -----------------------
@router.get("/", response_model=list[SupplierRead])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()

# -----------------------
# POST: Batch Resolve All Suppliers
# -----------------------
@router.post("/resolve_all", response_model=dict)
def batch_resolve_factors(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).filter(Supplier.industry_name != None).all()
    resolved_count = 0

    for supplier in suppliers:
        factor = resolve_supplier_factor(db, supplier)
        if factor:
            resolved_count += 1

    return {"total_suppliers": len(suppliers), "resolved": resolved_count}

# -----------------------
# DELETE: Delete Single Supplier
# -----------------------

@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: str, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(
        Supplier.supplier_id == supplier_id
    ).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found."
        )

    db.delete(supplier)
    db.commit()

    return None
