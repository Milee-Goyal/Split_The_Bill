import json
import os
import pytest
from app.schemas import ParsedBill

GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), "..", "test_bills", "ground_truth.json")


def load_all_ground_truth():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["bills"]


def test_ground_truth_contains_at_least_12_bills():
    bills = load_all_ground_truth()
    assert len(bills) >= 12, f"Expected at least 12 test bills, found {len(bills)}"


def test_ground_truth_pydantic_validation():
    bills = load_all_ground_truth()
    for bill_data in bills:
        # Validate that each bill strictly parses into ParsedBill model
        parsed = ParsedBill(**bill_data)
        assert parsed.bill_id == bill_data["bill_id"]
        assert len(parsed.items) > 0
        assert parsed.metadata.grand_total > 0
        # Check per-item confidences
        for item in parsed.items:
            assert 0.0 <= item.confidence <= 1.0


def test_bill_08_identifies_wrong_printed_total():
    bills = load_all_ground_truth()
    bill_8_data = next(b for b in bills if b["bill_id"] == "bill_08_wrong_printed_total")
    parsed = ParsedBill(**bill_8_data)

    # Must be flagged as invalid
    assert parsed.metadata.is_arithmetically_valid is False
    assert parsed.metadata.discrepancy_amount == pytest.approx(42.50, abs=0.5)


def test_dim_light_and_faded_thermal_have_lower_confidences():
    bills = load_all_ground_truth()
    bill_faded = next(b for b in bills if b["bill_id"] == "bill_04_faded_thermal")
    parsed = ParsedBill(**bill_faded)

    # Faded thermal items should reflect reduced OCR confidence (< 0.8)
    avg_conf = sum(it.confidence for it in parsed.items) / len(parsed.items)
    assert avg_conf < 0.80
