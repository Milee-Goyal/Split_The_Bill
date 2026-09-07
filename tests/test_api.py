import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import (
    ParsedBill,
    BillItem,
    BillMetadata,
    BillTaxes,
    ItemAssignment,
    SplitRequest,
)

client = TestClient(app)


def test_list_sample_bills_endpoint():
    res = client.get("/api/sample-bills")
    assert res.status_code == 200
    data = res.json()
    assert "bills" in data
    assert len(data["bills"]) >= 12
    # Check that bill_08_wrong_printed_total is marked invalid
    bill_8 = next(b for b in data["bills"] if b["bill_id"] == "bill_08_wrong_printed_total")
    assert bill_8["is_arithmetically_valid"] is False


def test_get_bill_detail_endpoint():
    res = client.get("/api/bills/bill_01_dim_light")
    assert res.status_code == 200
    data = res.json()
    assert data["bill_id"] == "bill_01_dim_light"
    assert len(data["items"]) == 4


def test_calculate_endpoint_api():
    bill = ParsedBill(
        bill_id="api_test_1",
        items=[
            BillItem(id="item_a", name="Burger", total_price=200.0),
            BillItem(id="item_b", name="Fries", total_price=100.0),
        ],
        metadata=BillMetadata(
            subtotal=300.0,
            taxes=BillTaxes(cgst=7.5, sgst=7.5),
            grand_total=315.0,
        )
    )

    req_payload = {
        "bill": bill.model_dump(),
        "members": ["Karan", "Simran"],
        "assignments": [
            {"item_id": "item_a", "assigned_to": ["Karan"], "is_all": False},
            {"item_id": "item_b", "assigned_to": ["Simran"], "is_all": False},
        ]
    }

    res = client.post("/api/calculate", json=req_payload)
    assert res.status_code == 200
    result = res.json()
    assert result["is_balanced"] is True
    assert result["bill_grand_total"] == 315.0

    member_map = {m["member_name"]: m for m in result["members"]}
    # Karan pays for Burger (200) + 2/3 of tax (10) = 210
    assert member_map["Karan"]["final_total"] == pytest.approx(210.0, abs=0.1)
    # Simran pays for Fries (100) + 1/3 of tax (5) = 105
    assert member_map["Simran"]["final_total"] == pytest.approx(105.0, abs=0.1)
