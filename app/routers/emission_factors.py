from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.category_factor_mapping import CategoryFactorMapping
from app.models.emission_factors import EmissionFactor
from app.schemas.emission_factors import EmissionFactorCreate
from app.services.emission_calculator import calculate_emissions
from app.routers.auth import get_current_user, User

router = APIRouter(prefix="/emission-factors", tags=["Emission Factors"])

class CategoryMapRequest(BaseModel):
    raw_category: str
    ceda_sector_code: str

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

@router.post("/map-category", response_model=dict)
def map_category(
    payload: CategoryMapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mapping = db.query(CategoryFactorMapping).filter(
        CategoryFactorMapping.category_id == payload.raw_category
    ).first()

    if mapping:
        mapping.emission_factor_id = payload.ceda_sector_code
        mapping.is_active = True
    else:
        mapping = CategoryFactorMapping(
            category_id=payload.raw_category,
            emission_factor_id=payload.ceda_sector_code,
            is_active=True
        )
        db.add(mapping)

    db.commit()

    updated_count = calculate_emissions(db)

    return {
        "message": "Mapping saved successfully",
        "records_updated": updated_count
    }
