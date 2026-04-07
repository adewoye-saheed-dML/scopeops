import uuid
from typing import Any

from rapidfuzz import process, fuzz
from sqlalchemy.orm import Session

from app.models.supplier import Supplier


def resolve_supplier(db: Session, raw_name: str, owner_id: uuid.UUID) -> dict[str, Any]:
    suppliers = (
        db.query(Supplier)
        .filter(Supplier.owner_id == owner_id)
        .all()
    )

    supplier_map = {
        supplier.supplier_name: supplier.id
        for supplier in suppliers
        if supplier.supplier_name
    }

    if not raw_name or not supplier_map:
        return {
            "match_found": False,
            "supplier_id": None,
            "confidence_score": 0.0,
            "status": "NEW_SUPPLIER",
        }

    match = process.extractOne(
        raw_name,
        supplier_map.keys(),
        scorer=fuzz.WRatio,
    )

    score = float(match[1]) if match else 0.0

    if score >= 90:
        status = "AUTO_MATCHED"
    elif score >= 70:
        status = "REQUIRES_REVIEW"
    else:
        status = "NEW_SUPPLIER"

    match_found = score >= 70
    supplier_id = supplier_map.get(match[0]) if match_found and match else None

    return {
        "match_found": match_found,
        "supplier_id": supplier_id,
        "confidence_score": score,
        "status": status,
    }
