def test_auth_flow(client):
    """Test Signup and Login to get Token."""
    res = client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "strongpassword123",
        "full_name": "Test User"
    })
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"

    res = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "strongpassword123"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token is not None
    return token

def test_create_supplier_and_spend(client):
    """Full flow: Auth -> Create Supplier -> Create Spend -> Get Summary."""
    token = test_auth_flow(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Supplier
    supplier_payload = {
        "supplier_name": "Acme Corp",
        "industry_locked": "Manufacturing",
        "region": "US"
    }
    res_sup = client.post("/suppliers/", json=supplier_payload, headers=headers)
    assert res_sup.status_code == 200
    supplier_id = res_sup.json()["id"]

    # 2. Add Spend Record
    spend_payload = {
        "supplier_id": supplier_id,
        "category_code": "DIRECT_MAT",
        "spend_amount": 5000.00,
        "currency": "USD",
        "fiscal_year": 2024
    }
    res_spend = client.post("/spend/", json=spend_payload, headers=headers)
    assert res_spend.status_code == 200
    assert float(res_spend.json()["spend_amount"]) == 5000.0

    # 3. Check Spend Summary (Using the updated "total_co2e" key)
    res_summary = client.get("/spend/summary", headers=headers)
    assert res_summary.status_code == 200
    data = res_summary.json()
    assert data["total_spend"] == 5000.0
    assert data["total_co2e"] == 0.0  # Changed from total_emissions to total_co2e

def test_supplier_isolation(client):
    """Test Multi-tenancy: User B cannot see User A's suppliers."""
    client.post("/auth/signup", json={"email": "userA@test.com", "password": "pw", "full_name": "A"})
    token_a = client.post("/auth/login", data={"username": "userA@test.com", "password": "pw"}).json()["access_token"]
    
    client.post("/auth/signup", json={"email": "userB@test.com", "password": "pw", "full_name": "B"})
    token_b = client.post("/auth/login", data={"username": "userB@test.com", "password": "pw"}).json()["access_token"]

    res = client.post("/suppliers/", json={"supplier_name": "User A Sup", "industry_locked": "Tech"}, headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    
    res_list = client.get("/suppliers/", headers={"Authorization": f"Bearer {token_b}"})
    assert res_list.status_code == 200
    assert len(res_list.json()) == 0