import pytest
from app.schemas import (
    BillItem,
    BillTaxes,
    BillMetadata,
    ParsedBill,
    ItemAssignment,
    SplitRequest,
)
from app.calculator import calculate_fair_split


def test_proportional_tax_split_not_equal():
    """
    Seven of you ate dinner:
    - Rahul and Priya shared Biryani (₹350) -> ₹175 each
    - Amit had only Coke (₹60)
    - Subtotal = ₹410
    - GST (5%) = ₹20.50
    - Total = ₹430.50

    Verifies Amit does NOT pay equal tax (20.50 / 3 = 6.83).
    Amit's food fraction = 60 / 410 = 14.634%
    Amit's fair tax = 20.50 * (60 / 410) = ₹3.00
    """
    bill = ParsedBill(
        bill_id="test_prop_1",
        bill_name="Biryani & Coke Test",
        items=[
            BillItem(id="i1", name="Chicken Biryani", quantity=1, unit_price=350.0, total_price=350.0),
            BillItem(id="i2", name="Diet Coke", quantity=1, unit_price=60.0, total_price=60.0),
        ],
        metadata=BillMetadata(
            restaurant_name="Spice Kitchen",
            subtotal=410.0,
            taxes=BillTaxes(cgst=10.25, sgst=10.25),
            grand_total=430.50,
        )
    )

    req = SplitRequest(
        bill=bill,
        members=["Rahul", "Priya", "Amit"],
        assignments=[
            ItemAssignment(item_id="i1", assigned_to=["Rahul", "Priya"]),
            ItemAssignment(item_id="i2", assigned_to=["Amit"]),
        ]
    )

    result = calculate_fair_split(req)

    assert result.is_balanced is True
    assert result.total_allocated == 430.50

    shares = {m.member_name: m for m in result.members}
    assert shares["Amit"].food_subtotal == 60.0
    # Amit's tax should be around 3.00 (proportionate), far less than equal share 6.83
    assert shares["Amit"].tax_share == pytest.approx(3.00, abs=0.05)
    assert shares["Amit"].final_total < 65.0

    # Rahul and Priya should pay identical amounts
    assert shares["Rahul"].final_total == pytest.approx(shares["Priya"].final_total, abs=0.05)
    assert round(shares["Rahul"].final_total + shares["Priya"].final_total + shares["Amit"].final_total, 2) == 430.50


def test_shared_all_items():
    bill = ParsedBill(
        bill_id="test_all_1",
        items=[
            BillItem(id="i1", name="Pizza", total_price=300.0),
            BillItem(id="i2", name="Garlic Bread", total_price=100.0),
        ],
        metadata=BillMetadata(
            subtotal=400.0,
            taxes=BillTaxes(service_charge=40.0, cgst=10.0, sgst=10.0),
            grand_total=460.0,
        )
    )
    req = SplitRequest(
        bill=bill,
        members=["Alice", "Bob"],
        assignments=[
            ItemAssignment(item_id="i1", is_all=True),
            ItemAssignment(item_id="i2", is_all=True),
        ]
    )
    res = calculate_fair_split(req)
    assert res.is_balanced is True
    assert res.total_allocated == 460.0
    for m in res.members:
        assert m.final_total == 230.0


def test_discrepancy_detection_on_wrong_total():
    """
    Tests bill where printed total is intentionally wrong (arithmetic discrepancy).
    """
    bill = ParsedBill(
        bill_id="test_wrong_total",
        items=[
            BillItem(id="i1", name="Burger", total_price=100.0),
        ],
        metadata=BillMetadata(
            subtotal=100.0,
            taxes=BillTaxes(cgst=5.0, sgst=5.0),
            grand_total=130.0,  # Should be 110.0, printed total is +20 too high
        )
    )
    # The Pydantic model validator should automatically flag it
    assert bill.metadata.is_arithmetically_valid is False
    assert bill.metadata.discrepancy_amount == 20.0
