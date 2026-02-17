from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.emission_factors import EmissionFactor
from app.schemas.emission_factors import EmissionFactorCreate

router = APIRouter(prefix="/emission-factors", tags=["Emission Factors"])


@router.post("/")
def create_factor(payload: EmissionFactorCreate, db: Session = Depends(get_db)):
    try:
        factor = EmissionFactor(**payload.dict())
        db.add(factor)
        db.commit()
        db.refresh(factor)
        return factor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Factor creation failed")


@router.get("/")
def list_factors(db: Session = Depends(get_db)):
    return db.query(EmissionFactor).all()
