import uuid
from app.models.supplier import Supplier
from app.models.spend import SpendRecord
from app.models.emission_factors import EmissionFactor
from app.models.user import User
from app.services.parent_child_circular import creates_cycle
from app.services.emission_calculator import calculate_emissions
from app.services.supplier_factor import resolve_supplier_factor

def test_circular_dependency_check(db_session):
    """Test that A -> B -> A is detected as a cycle."""
    user_id = uuid.uuid4()
    
    # Create Supplier A and B
    sup_a = Supplier(id=uuid.uuid4(), supplier_name="Supplier A", industry_locked="Tech", owner_id=user_id)
    sup_b = Supplier(id=uuid.uuid4(), supplier_name="Supplier B", industry_locked="Tech", owner_id=user_id)
    
    db_session.add_all([sup_a, sup_b])
    db_session.commit()

    # Set B as child of A (A -> B)
    sup_b.parent_id = sup_a.id
    db_session.commit()

    # Attempt to make A a child of B (B -> A), should return True (Cycle detected)
    is_cycle = creates_cycle(db_session, child_id=sup_a.id, parent_id=sup_b.id)
    assert is_cycle is True

    # Attempt valid hierarchy (C -> B), should return False
    sup_c = Supplier(id=uuid.uuid4(), supplier_name="Supplier C", industry_locked="Tech", owner_id=user_id)
    db_session.add(sup_c)
    db_session.commit()
    
    is_cycle_safe = creates_cycle(db_session, child_id=sup_c.id, parent_id=sup_b.id)
    assert is_cycle_safe is False

def test_resolve_verified_supplier_factor(db_session):
    """Test that 'Nike Inc' gets the verified hardcoded factor."""
    user_id = uuid.uuid4()
    
    # Create 'Nike Inc' supplier
    nike = Supplier(id=uuid.uuid4(), supplier_name="Nike Inc", domain="nike.com", industry_locked="Apparel", owner_id=user_id)
    db_session.add(nike)
    db_session.commit()

    # Run resolution logic
    factor = resolve_supplier_factor(db_session, nike)

    assert factor is not None
    assert factor.provider == "Verified Supplier Disclosure"
    assert "Nike" in factor.name
    # Verify factor was actually linked
    assert nike.resolved_factor_id == factor.id

def test_emission_calculation_logic(db_session):
    """Test that spend * factor = emission."""
    user_id = uuid.uuid4()
    
    # 1. Create a Factor
    factor = EmissionFactor(
        id=uuid.uuid4(),
        name="Test Factor",
        provider="Test",
        geography="US",
        year=2024,
        co2e_per_currency=0.5, # 0.5 kg CO2 per Dollar
        version="1",
        owner_id=user_id
    )
    
    # 2. Create Supplier linked to Factor
    supplier = Supplier(
        id=uuid.uuid4(), 
        supplier_name="Test Supplier", 
        industry_locked="Test", 
        resolved_factor_id=factor.id,
        owner_id=user_id
    )
    
    # 3. Create Spend Record (Uncalculated)
    spend = SpendRecord(
        spend_id=1,
        supplier_id=supplier.id,
        category_code="IT",
        spend_amount=1000.00,
        currency="USD",
        fiscal_year=2024,
        owner_id=user_id
    )

    db_session.add_all([factor, supplier, spend])
    db_session.commit()

    # 4. Run Calculation Service
    updated_count = calculate_emissions(db_session)

    assert updated_count == 1
    db_session.refresh(spend)
    
    # Expect: 1000 * 0.5 = 500.0
    assert spend.calculated_co2e == 500.0
    assert spend.calculation_method == "Supplier_Locked"