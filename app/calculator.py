from typing import List, Dict
from app.schemas import (
    ParsedBill,
    SplitRequest,
    SplitResponse,
    MemberShare,
    ConsumedItemDetail,
    ItemAssignment,
)


def calculate_fair_split(request: SplitRequest) -> SplitResponse:
    """
    Computes mathematically fair proportional bill split:
    1. Determines item level allocations (single person, multiple people, or all).
    2. Calculates personal food subtotal per person.
    3. Allocates taxes, service charge, and discounts proportionally based on food subtotal fraction.
    4. Applies penny/paise rounding correction so sum(members) == bill.grand_total.
    """
    bill = request.bill
    members = [m.strip() for m in request.members if m.strip()]
    if not members:
        raise ValueError("At least one member must be provided.")

    # Index assignments by item_id
    assignment_map: Dict[str, ItemAssignment] = {a.item_id: a for a in request.assignments}

    # Initialize data structures for each member
    member_items: Dict[str, List[ConsumedItemDetail]] = {m: [] for m in members}
    member_subtotals: Dict[str, float] = {m: 0.0 for m in members}

    # Assign each bill item
    for item in bill.items:
        assignment = assignment_map.get(item.id)

        target_members: List[str] = []
        if assignment:
            if assignment.is_all:
                target_members = members.copy()
            else:
                # Filter to valid members present in the member list
                target_members = [m for m in assignment.assigned_to if m in members]

        # If no one assigned, default to sharing among everyone
        if not target_members:
            target_members = members.copy()

        split_count = len(target_members)
        split_ratio = 1.0 / split_count
        charge_per_person = round(item.total_price * split_ratio, 2)

        # Ensure sum of split item equals item.total_price exactly
        split_charges = [charge_per_person] * split_count
        remainder = round(item.total_price - sum(split_charges), 2)
        if remainder != 0:
            split_charges[0] = round(split_charges[0] + remainder, 2)

        for i, m in enumerate(target_members):
            charge = split_charges[i]
            member_items[m].append(
                ConsumedItemDetail(
                    item_id=item.id,
                    item_name=item.name,
                    item_total_price=item.total_price,
                    split_ratio=round(split_ratio, 4),
                    member_charge=charge,
                )
            )
            member_subtotals[m] = round(member_subtotals[m] + charge, 2)

    total_food_subtotal = round(sum(member_subtotals.values()), 2)

    # Taxes & Fees from metadata
    taxes_obj = bill.metadata.taxes
    total_tax = round(taxes_obj.cgst + taxes_obj.sgst + taxes_obj.vat, 2)
    service_charge = round(taxes_obj.service_charge, 2)
    discount = round(taxes_obj.discount, 2)
    other_charges = round(taxes_obj.other_charges, 2)

    member_shares: List[MemberShare] = []

    for m in members:
        food_sub = member_subtotals[m]
        spend_frac = (food_sub / total_food_subtotal) if total_food_subtotal > 0 else (1.0 / len(members))
        spend_frac = round(spend_frac, 6)

        # Proportional distribution of taxes, service charge, and discounts
        tax_share = round(total_tax * spend_frac, 2)
        sc_share = round(service_charge * spend_frac, 2)
        disc_share = round(discount * spend_frac, 2)
        other_share = round(other_charges * spend_frac, 2)

        final_amount = round(food_sub + tax_share + sc_share + other_share - disc_share, 2)

        member_shares.append(
            MemberShare(
                member_name=m,
                items_consumed=member_items[m],
                food_subtotal=food_sub,
                spend_fraction=round(spend_frac, 4),
                tax_share=tax_share,
                service_charge_share=sc_share,
                discount_share=disc_share,
                other_charges_share=other_share,
                final_total=final_amount,
            )
        )

    # Exact reconciliation to the printed grand total
    target_grand_total = bill.metadata.grand_total
    current_allocated = round(sum(ms.final_total for ms in member_shares), 2)
    rounding_diff = round(target_grand_total - current_allocated, 2)

    # If within reasonable rounding tolerance (+/- 1.0 currency unit), adjust to highest spender
    if abs(rounding_diff) > 0 and abs(rounding_diff) <= 1.0 and member_shares:
        # Sort by food_subtotal descending to give rounding adjustment to largest ticket
        highest_spender = max(member_shares, key=lambda s: s.food_subtotal)
        highest_spender.final_total = round(highest_spender.final_total + rounding_diff, 2)
        current_allocated = round(sum(ms.final_total for ms in member_shares), 2)

    is_balanced = abs(round(current_allocated - target_grand_total, 2)) < 0.01

    notes = None
    if not bill.metadata.is_arithmetically_valid:
        notes = f"Warning: Bill printed total differs from computed items + taxes by {bill.metadata.discrepancy_amount:+.2f}."

    return SplitResponse(
        bill_id=bill.bill_id,
        bill_grand_total=target_grand_total,
        total_allocated=current_allocated,
        rounding_adjustment=rounding_diff,
        is_balanced=is_balanced,
        members=member_shares,
        notes=notes,
    )
