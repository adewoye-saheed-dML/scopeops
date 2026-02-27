import csv
import io
import uuid
import random
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
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

@router.post("/bulk-upload", response_model=dict)
async def bulk_upload_spend(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are permitted.")

    # Read and decode the file
    content = await file.read()
    try:
        # utf-8-sig automatically handles the BOM (Byte Order Mark) if exported from Excel
        text_content = content.decode("utf-8-sig") 
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 CSV.")

    reader = csv.DictReader(io.StringIO(text_content))
    
    # Pre-fetch user's suppliers for fast, in-memory permission checking
    user_suppliers = {str(s.id) for s in db.query(Supplier.id).filter(Supplier.owner_id == current_user.id).all()}

    records_to_insert = []
    errors = []
    row_number = 1  

    # Helper function to convert empty CSV strings to None
    def clean_val(v):
        return v.strip() if v and v.strip() else None

    for row in reader:
        row_number += 1
        
        supplier_id = clean_val(row.get("supplier_id"))
        if not supplier_id or supplier_id not in user_suppliers:
            errors.append(f"Row {row_number}: Invalid or unauthorized supplier_id.")
            continue

        try:
            # Leverage the existing Pydantic model to validate the row exactly like a normal POST
            payload = SpendCreate(
                supplier_id=supplier_id,
                category_code=clean_val(row.get("category_code")),
                fiscal_year=clean_val(row.get("fiscal_year")),
                spend_amount=clean_val(row.get("spend_amount")),
                currency=clean_val(row.get("currency")),
                quantity=clean_val(row.get("quantity")),
                unit_of_measure=clean_val(row.get("unit_of_measure")),
                material_type=clean_val(row.get("material_type")),
                factor_used_id=clean_val(row.get("factor_used_id"))
            )
            
            records_to_insert.append(SpendRecord(**payload.dict(), owner_id=current_user.id))
            
        except ValidationError as e:
            error_msg = e.errors()[0]["msg"]
            field = e.errors()[0]["loc"][0]
            errors.append(f"Row {row_number}: Field '{field}' - {error_msg}")
        except Exception as e:
            errors.append(f"Row {row_number}: Unexpected error - {str(e)}")

    # Bulk insert valid records
    if records_to_insert:
        try:
            db.add_all(records_to_insert)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error during bulk insert.")

    # Return a summary report
    return {
        "message": "Bulk upload processed",
        "inserted_count": len(records_to_insert),
        "error_count": len(errors),
        "errors": errors[:50]  
    }

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


@router.post("/seed-demo-data", response_model=dict)
def seed_demo_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Prevent double-seeding if the user already has data
    existing_supplier = db.query(Supplier).filter(Supplier.owner_id == current_user.id).first()
    if existing_supplier:
        return {"message": "Demo data already exists for this user."}

    # Create Realistic Suppliers
    s1_id = uuid.uuid4()
    s2_id = uuid.uuid4()
    s3_id = uuid.uuid4()
    s4_id = uuid.uuid4()

    demo_suppliers = [
        Supplier(id=s1_id, supplier_name="Amazon Web Services", industry_locked="Cloud Infrastructure", domain="aws.amazon.com", region="Global", has_disclosure=True, owner_id=current_user.id),
        Supplier(id=s2_id, supplier_name="FedEx Logistics", industry_locked="Transportation", domain="fedex.com", region="North America", has_disclosure=False, owner_id=current_user.id),
        Supplier(id=s3_id, supplier_name="Dell Technologies", industry_locked="Hardware", domain="dell.com", region="Global", has_disclosure=True, owner_id=current_user.id),
        Supplier(id=s4_id, supplier_name="WeWork", industry_locked="Real Estate", domain="wework.com", region="Global", has_disclosure=False, owner_id=current_user.id)
    ]
    db.add_all(demo_suppliers)
    db.flush() 

    # Create Realistic Spend Records
    demo_records = []
    supplier_mapping = [
        (s1_id, "IT_INFRASTRUCTURE"),
        (s2_id, "LOGISTICS_FREIGHT"),
        (s3_id, "OFFICE_EQUIPMENT"),
        (s4_id, "FACILITIES_RENT")
    ]

    # Generate 15 random records to make the charts look good
    for _ in range(15):
        sup_id, category = random.choice(supplier_mapping)
        spend = Decimal(random.randint(5000, 150000))
        
        # Calculate total lump sum
        co2e = spend * Decimal(random.uniform(0.01, 0.05)) 
        
        # Distribute realistically across scopes
        scope_1 = co2e * Decimal(random.uniform(0.02, 0.08))  
        scope_2 = co2e * Decimal(random.uniform(0.05, 0.15))  
        scope_3 = co2e - scope_1 - scope_2                    
        
        demo_records.append(
            SpendRecord(
                supplier_id=sup_id,
                category_code=category,
                fiscal_year=datetime.utcnow().year,
                spend_amount=spend,
                currency="USD",
                calculated_co2e=co2e,
                calculated_scope_1=scope_1,
                calculated_scope_2=scope_2,
                calculated_scope_3=scope_3,
                owner_id=current_user.id
            )
        )

    db.add_all(demo_records)
    db.commit()

    return {"message": "Demo data successfully loaded"}