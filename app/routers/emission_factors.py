from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.emission_factors import EmissionFactor
from app.schemas.emission_factors import EmissionFactorCreate
from app.routers.auth import get_current_user, User

router = APIRouter(prefix="/emission-factors", tags=["Emission Factors"])

@router.post("/")
def create_factor(
    payload: EmissionFactorCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Create factor assigned to this user
        factor = EmissionFactor(**payload.dict(), owner_id=current_user.id)
        db.add(factor)
        db.commit()
        db.refresh(factor)
        return factor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Factor creation failed")

@router.get("/")
def list_factors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Return Global factors (owner_id is NULL) OR User's private factors
    return db.query(EmissionFactor).filter(
        or_(
            EmissionFactor.owner_id == None, 
            EmissionFactor.owner_id == current_user.id
        )
    ).all()