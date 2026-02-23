from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.database import get_db
from app.models.spend import SpendRecord
from app.models.supplier import Supplier
from app.schemas.spend import SpendCreate, SpendRead
from app.services.emission_calculator import calculate_emissions
from app.routers.auth import get_current_user, User

router = APIRouter(prefix="/spend", tags=["Spend"])

@router.post("/", response_model=SpendRead)
def create_spend(
    payload: SpendCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    supplier = db.query(Supplier).filter(
        Supplier.id == payload.supplier_id, 
        Supplier.owner_id == current_user.id
    ).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier not found or does not belong to the current user."
        )
        
    try:
        record = SpendRecord(**payload.dict(), owner_id=current_user.id)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Data Integrity"
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

@router.post("/calculate", response_model=dict)
def run_batch_calculation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = calculate_emissions(db) 
    return {"records_updated": updated}

@router.get("/summary", response_model=dict)
def spend_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Financial Totals
    total_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).filter(SpendRecord.owner_id == current_user.id).scalar()

    # Emission Totals
    total_emissions = db.query(
        func.coalesce(func.sum(SpendRecord.calculated_co2e), 0)
    ).filter(SpendRecord.owner_id == current_user.id).scalar()

    # --- Scope Breakdowns ---
    total_scope_1 = db.query(
        func.coalesce(func.sum(SpendRecord.calculated_scope_1), 0)
    ).filter(SpendRecord.owner_id == current_user.id).scalar()
    
    total_scope_2 = db.query(
        func.coalesce(func.sum(SpendRecord.calculated_scope_2), 0)
    ).filter(SpendRecord.owner_id == current_user.id).scalar()
    
    total_scope_3 = db.query(
        func.coalesce(func.sum(SpendRecord.calculated_scope_3), 0)
    ).filter(SpendRecord.owner_id == current_user.id).scalar()

    # Record Tracking
    records_calculated = db.query(SpendRecord).filter(
        SpendRecord.calculated_co2e != None,
        SpendRecord.owner_id == current_user.id
    ).count()

    records_uncalculated = db.query(SpendRecord).filter(
        SpendRecord.calculated_co2e == None,
        SpendRecord.owner_id == current_user.id
    ).count()

    emission_intensity = float(total_emissions) / float(total_spend) if total_spend else 0

    return {
        "total_spend": float(total_spend),
        "total_emissions": float(total_emissions),
        "total_scope_1": float(total_scope_1),
        "total_scope_2": float(total_scope_2),
        "total_scope_3": float(total_scope_3),
        "emission_intensity": emission_intensity,
        "records_calculated": records_calculated,
        "records_uncalculated": records_uncalculated
    }

@router.get("/coverage", response_model=dict)
def spend_coverage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).filter(SpendRecord.owner_id == current_user.id).scalar()

    covered_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).filter(
        SpendRecord.factor_used_id != None,
        SpendRecord.owner_id == current_user.id
    ).scalar()

    coverage_percentage = (float(covered_spend) / float(total_spend) * 100) if total_spend else 0

    return {
        "total_spend": float(total_spend),
        "covered_spend": float(covered_spend),
        "coverage_percentage": coverage_percentage
    }