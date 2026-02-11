from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.spend import SpendRecord
from app.schemas.spend import SpendCreate, SpendRead

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