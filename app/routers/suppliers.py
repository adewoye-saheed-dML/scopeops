
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierRead
from app.routers.auth import get_current_user, User
from app.services.tree_rollup import get_supplier_tree_rollup
from app.services.parent_child_circular import creates_cycle

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("/", response_model=SupplierRead)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
                    #current_user: User = Depends(get_current_user)):
    try:
        # Validate parent_id if provided
        if payload.parent_id:
            parent = db.query(Supplier).filter(
                Supplier.id == payload.parent_id
            ).first()

            if not parent:
                raise HTTPException(
                    status_code=400,
                    detail="Parent supplier not found"
                )
        # create new supplier
        supplier = Supplier(**payload.dict())

        # prevent self-parenting
        if supplier.parent_id and supplier.parent_id == supplier.id:
            raise HTTPException(
                status_code=400,
                detail="Supplier cannot be its own parent"
            )
        # prevent circular dependency
        if supplier.parent_id and creates_cycle(
            db,
            child_id=supplier.id,
            parent_id=supplier.parent_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Circular supplier hierarchy detected"
            )
        
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        return supplier
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Supplier already exists")


@router.get("/", response_model=list[SupplierRead])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()


@router.get("/suppliers/{supplier_id}/enterprise-rollup")
def enterprise_rollup(supplier_id: str, db: Session = Depends(get_db)):
    return get_supplier_tree_rollup(db, supplier_id)



@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: str, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db.delete(supplier)
    db.commit()
    return {"message": "Deleted"}
