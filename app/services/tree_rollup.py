from sqlalchemy import select, union_all
from sqlalchemy.orm import aliased
from sqlalchemy.sql import literal_column
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.supplier import Supplier
from app.models.spend import SpendRecord


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
