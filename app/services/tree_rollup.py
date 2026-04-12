from sqlalchemy import select, func
from sqlalchemy.orm import aliased, Session
from app.models.supplier import Supplier
from app.models.spend import SpendRecord
from app.models.emission_factors import EmissionFactor

def get_supplier_tree_rollup(db: Session, supplier_id: str):
    supplier_alias = aliased(Supplier)

    # Base query
    supplier_tree = select(Supplier.id).where(
        Supplier.id == supplier_id
    ).cte(name="supplier_tree", recursive=True)

    # Recursive part
    supplier_tree = supplier_tree.union_all(
        select(supplier_alias.id).where(
            supplier_alias.parent_id == supplier_tree.c.id
        )
    )

    # Rollup spend
    total_spend = db.query(
        func.coalesce(func.sum(SpendRecord.spend_amount), 0)
    ).filter(
        SpendRecord.supplier_id.in_(
            select(supplier_tree.c.id)
        )
    ).scalar()

    # Rollup emissions
    total_emissions = db.query(
        func.coalesce(func.sum(SpendRecord.calculated_co2e), 0)
    ).filter(
        SpendRecord.supplier_id.in_(
            select(supplier_tree.c.id)
        )
    ).scalar()

    return {
        "supplier_id": supplier_id,
        "total_spend": float(total_spend),
        "total_emissions": float(total_emissions)
    }

def get_effective_factor(db: Session, supplier_id: str):
    """
    Traverse up the supplier corporate tree to find the nearest assigned emission factor.
    """
    current_id = supplier_id
    visited = set()

    while current_id:
        if current_id in visited:
            break  # Prevent infinite loops in case of circular dependencies
        visited.add(current_id)

        supplier = db.query(Supplier).filter(Supplier.id == current_id).first()
        if not supplier:
            break

        # If this supplier in the tree has a locked factor, return it
        if supplier.resolved_factor_id:
            factor = db.query(EmissionFactor).filter(EmissionFactor.id == supplier.resolved_factor_id).first()
            if factor:
                return factor

        # Move up to the parent
        current_id = supplier.parent_id

    return None