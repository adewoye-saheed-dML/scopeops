from rapidfuzz import process
from sqlalchemy.orm import Session
from app.models.supplier import Supplier
from app.config.verified_suppliers import VERIFIED_SUPPLIERS



def creates_cycle(db: Session, child_id, parent_id) -> bool:
    """
    Returns True if assigning parent_id to child_id creates a cycle.
    """
    current_parent = parent_id

    while current_parent:
        if current_parent == child_id:
            return True

        parent = db.query(Supplier).filter(
            Supplier.id == current_parent
        ).first()

        if not parent:
            break

        current_parent = parent.parent_id

    return False
