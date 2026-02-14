from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.spend import SpendRecord
from app.schemas.spend import SpendCreate, SpendRead
from app.services.emission_calculator import calculate_emissions
from app.models.supplier import Supplier
from sqlalchemy import func


router = APIRouter(prefix="/spend", tags=["Spend"])

@router.post("/", response_model=SpendRead)
def create_spend(payload: SpendCreate, db: Session = Depends(get_db)):
    try:
        record = SpendRecord(**payload.dict())
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid Foreign Key: Supplier does not exist."
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal Server Error"
        )

@router.post("/calculate", response_model=dict)
def run_batch_calculation(db: Session = Depends(get_db)):
    updated = calculate_emissions(db)
    return {"records_updated": updated}




@router.get("/summary", response_model=dict)
def spend_summary(db: Session = Depends(get_db)):

    total_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).scalar()

    total_emissions = db.query(
        func.coalesce(func.sum(SpendRecord.calculated_co2e), 0)
    ).scalar()

    records_calculated = db.query(SpendRecord).filter(
        SpendRecord.calculated_co2e != None
    ).count()

    records_uncalculated = db.query(SpendRecord).filter(
        SpendRecord.calculated_co2e == None
    ).count()

    emission_intensity = 0
    if total_spend and total_spend != 0:
        emission_intensity = float(total_emissions) / float(total_spend)

    return {
        "total_spend": float(total_spend),
        "total_emissions": float(total_emissions),
        "emission_intensity": emission_intensity,
        "records_calculated": records_calculated,
        "records_uncalculated": records_uncalculated
    }


@router.get("/coverage", response_model=dict)
def spend_coverage(db: Session = Depends(get_db)):

    total_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).scalar()

    covered_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).join(
        Supplier,
        SpendRecord.supplier_id == Supplier.supplier_id
    ).filter(
        Supplier.resolved_factor_id != None
    ).scalar()

    coverage_percentage = 0
    if total_spend and total_spend != 0:
        coverage_percentage = (float(covered_spend) / float(total_spend)) * 100

    return {
        "total_spend": float(total_spend),
        "covered_spend": float(covered_spend),
        "coverage_percentage": coverage_percentage
    }

