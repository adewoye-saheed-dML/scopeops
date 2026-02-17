from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.database import get_db
from app.models.spend import SpendRecord
from app.schemas.spend import SpendCreate, SpendRead
from app.services.emission_calculator import calculate_emissions
from app.routers.auth import get_current_user, User



router = APIRouter(prefix="/spend", tags=["Spend"])


@router.post("/", response_model=SpendRead)
def create_spend(payload: SpendCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
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
def run_batch_calculation(db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    updated = calculate_emissions(db)
    return {"records_updated": updated}



@router.get("/summary", response_model=dict)
def spend_summary(db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):

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

    emission_intensity = float(total_emissions) / float(total_spend) if total_spend else 0

    return {
        "total_spend": float(total_spend),
        "total_emissions": float(total_emissions),
        "emission_intensity": emission_intensity,
        "records_calculated": records_calculated,
        "records_uncalculated": records_uncalculated
    }



@router.get("/coverage", response_model=dict)
def spend_coverage(db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):

    total_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).scalar()

    covered_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).filter(
        SpendRecord.factor_used_id != None
    ).scalar()

    coverage_percentage = (float(covered_spend) / float(total_spend) * 100) if total_spend else 0

    return {
        "total_spend": float(total_spend),
        "covered_spend": float(covered_spend),
        "coverage_percentage": coverage_percentage
    }
