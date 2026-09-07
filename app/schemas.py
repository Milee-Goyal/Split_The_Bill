from typing import List, Dict, Optional
from pydantic import BaseModel, Field, model_validator


class BillItem(BaseModel):
    id: str = Field(..., description="Unique identifier for the item (e.g. item_1)")
    name: str = Field(..., description="Description/Name of the food or drink item")
    quantity: float = Field(default=1.0, ge=0.1, description="Quantity ordered")
    unit_price: float = Field(default=0.0, ge=0.0, description="Price per single unit")
    total_price: float = Field(..., ge=0.0, description="Total price for this line item (quantity * unit_price)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score from OCR/Vision (0.0 to 1.0)")


class BillTaxes(BaseModel):
    cgst: float = Field(default=0.0, ge=0.0, description="Central GST amount")
    sgst: float = Field(default=0.0, ge=0.0, description="State GST amount")
    vat: float = Field(default=0.0, ge=0.0, description="VAT or Liquor tax amount")
    service_charge: float = Field(default=0.0, ge=0.0, description="Restaurant service charge or tip")
    discount: float = Field(default=0.0, ge=0.0, description="Discount deducted from bill")
    other_charges: float = Field(default=0.0, ge=0.0, description="Packaging, delivery, or roundoff")

    @property
    def total_tax_and_fees(self) -> float:
        return round(self.cgst + self.sgst + self.vat + self.service_charge + self.other_charges, 2)


class BillMetadata(BaseModel):
    restaurant_name: Optional[str] = Field(default="Restaurant", description="Name of restaurant/cafe")
    date: Optional[str] = Field(default=None, description="Date of receipt")
    subtotal: float = Field(..., ge=0.0, description="Subtotal before taxes and discounts")
    taxes: BillTaxes = Field(default_factory=BillTaxes)
    grand_total: float = Field(..., ge=0.0, description="Final payable total printed on receipt")
    is_arithmetically_valid: bool = Field(default=True, description="Whether items + taxes - discount equals printed grand total")
    discrepancy_amount: float = Field(default=0.0, description="Difference between calculated total and printed total if invalid")
    field_confidences: Dict[str, float] = Field(default_factory=dict, description="Confidence scores per metadata field")


class ParsedBill(BaseModel):
    bill_id: str = Field(..., description="Identifier of the bill")
    bill_name: str = Field(default="Uploaded Bill", description="Friendly title")
    image_url: Optional[str] = Field(default=None, description="Relative path or URL to receipt image")
    items: List[BillItem] = Field(default_factory=list, description="Extracted line items")
    metadata: BillMetadata = Field(..., description="Bill totals, taxes, and validity metadata")
    condition_tag: Optional[str] = Field(default="Standard", description="Edge case tag (e.g. Faded, Crumpled, Handwritten)")

    @model_validator(mode="after")
    def validate_arithmetic(self) -> "ParsedBill":
        items_sum = round(sum(item.total_price for item in self.items), 2)
        expected_total = round(
            self.metadata.subtotal 
            + self.metadata.taxes.cgst 
            + self.metadata.taxes.sgst 
            + self.metadata.taxes.vat 
            + self.metadata.taxes.service_charge 
            + self.metadata.taxes.other_charges 
            - self.metadata.taxes.discount, 
            2
        )
        diff = round(abs(expected_total - self.metadata.grand_total), 2)
        # Check tolerance of 1.0 currency unit for typical printed roundoff
        if diff > 1.0:
            self.metadata.is_arithmetically_valid = False
            self.metadata.discrepancy_amount = round(self.metadata.grand_total - expected_total, 2)
        else:
            self.metadata.is_arithmetically_valid = True
            self.metadata.discrepancy_amount = 0.0
        return self


class ItemAssignment(BaseModel):
    item_id: str
    assigned_to: List[str] = Field(default_factory=list, description="Names of members sharing this item")
    is_all: bool = Field(default=False, description="Whether this item is shared by everyone")


class SplitRequest(BaseModel):
    bill: ParsedBill
    members: List[str] = Field(..., min_length=1, description="List of participant names")
    assignments: List[ItemAssignment] = Field(default_factory=list, description="Assignments per item")


class ConsumedItemDetail(BaseModel):
    item_id: str
    item_name: str
    item_total_price: float
    split_ratio: float = Field(..., description="Fraction of item borne by this member (e.g. 0.5 for 2 people)")
    member_charge: float = Field(..., description="Charge for this item for this member")


class MemberShare(BaseModel):
    member_name: str
    items_consumed: List[ConsumedItemDetail] = Field(default_factory=list)
    food_subtotal: float = Field(default=0.0, description="Personal food subtotal")
    spend_fraction: float = Field(default=0.0, description="Fraction of total food subtotal")
    tax_share: float = Field(default=0.0, description="Proportional share of CGST + SGST + VAT")
    service_charge_share: float = Field(default=0.0, description="Proportional share of service charge")
    discount_share: float = Field(default=0.0, description="Proportional share of discount (deducted)")
    other_charges_share: float = Field(default=0.0, description="Proportional share of misc charges")
    final_total: float = Field(default=0.0, description="Total amount this member pays")


class SplitResponse(BaseModel):
    bill_id: str
    bill_grand_total: float
    total_allocated: float
    rounding_adjustment: float = Field(default=0.0, description="Adjustment in paise/cents applied to ensure exact match")
    is_balanced: bool = Field(default=True, description="True if sum of members equals bill grand total")
    members: List[MemberShare]
    notes: Optional[str] = None
