# Split the Bill From a Photograph

A computer vision and deterministic arithmetic system that parses restaurant receipts, validates line-item confidence scores, supports interactive participant assignment via member chips, and computes mathematically fair proportional tax and service charge allocations.

---

## Key Features

1. **Structured Receipt Extraction (Upload and Live Camera)**:
   - Ingestion via file upload (PNG/JPG) or real-time camera capture.
   - Structured parsing into Pydantic v2 data models (`BillItem`, `BillTaxes`, `BillMetadata`, `ParsedBill`).
   - Extracts line items, quantities, unit prices, total prices, subtotals, CGST/SGST/VAT, service charges, discounts, and grand totals.
   - Computes per-field OCR confidence metrics (0.0 to 1.0).

2. **Human-in-the-Loop Verification**:
   - Side-by-side review interface displaying original receipt image alongside an editable data table.
   - Flags low-confidence extractions (confidence < 85%) for human review.
   - **Cashier Discrepancy Detection**: Cross-checks expected totals against printed totals to detect vendor arithmetic errors:
     $$|G_{\text{printed}} - G_{\text{expected}}| > 1.00$$

3. **Interactive Participant Assignment (Way A - Chips)**:
   - Dynamic participant pool (starts empty for manual user entry).
   - Per-item interactive chips to allocate dishes to all members or subsets of participants.
   - Real-time spend ticker recalculating individual balances upon chip toggles.

4. **Proportional Expense Allocation**:
   - Eliminates naive equal tax distribution. Taxes, discounts, and service charges are allocated strictly according to individual food consumption ratios:
     $$r_i = \frac{S_i}{\sum S_j}, \quad T_i = T_{\text{total}} \cdot r_i$$
   - Zero-residual penny reconciliation algorithm ensures:
     $$\sum_{i=1}^{M} \text{Payable}_i \equiv G_{\text{printed}}$$

5. **Benchmark Test Suite (12 Edge Cases)**:
   - Dedicated evaluation view containing 12 challenging real-world receipt conditions with hand-annotated ground truths in `test_bills/ground_truth.json`.

---

## Mathematical Formulation

### The Problem with Naive Equal Allocation:
Consider two diners:
- Person A consumes 700.00 in food.
- Person B consumes 100.00 in beverages.
- Food Subtotal = 800.00. Taxes and Service Charge (15%) = 120.00. Grand Total = 920.00.

* **Naive Split**: Taxes divided equally (120 / 2 = 60.00 each). Person B pays 160.00 (an effective 60% tax rate on a 100.00 beverage).
* **Proportional Engine**:
  $$S_i = \sum_{k \in \text{Items}_i} \frac{P_k}{N_k}$$
  $$r_i = \frac{S_i}{S_{\text{total}}}$$
  $$T_i = T_{\text{total}} \cdot r_i$$
  - Person B: $r_B = 100 / 800 = 0.125 \implies \text{Tax} = 120 \times 0.125 = 15.00 \implies \text{Total} = 115.00$
  - Person A: $r_A = 700 / 800 = 0.875 \implies \text{Tax} = 120 \times 0.875 = 105.00 \implies \text{Total} = 805.00$
  - Sum of shares equals 920.00 exactly.

---

## Mocked vs. Live Components

To ensure complete, deterministic reproducibility without requiring external paid API keys:
- **Vision AI Pipeline**: If `GEMINI_API_KEY` or `OPENAI_API_KEY` is provided in the environment, `/api/upload` queries the respective multimodal vision model (`gemini-1.5-flash` or `gpt-4o`).
- **Offline Benchmark Mode (Default)**: Pre-configured with 12 challenging edge-case receipts and hand-annotated ground truths in `test_bills/ground_truth.json`. Selecting any benchmark card loads authentic image previews, extracted line items, and realistic confidence scores.
- **Deterministic Core**: Schema validation, arithmetic verification, member chip assignment, and proportional calculation engines run live production code in all modes.

---

## Benchmark Dataset (12 Challenging Edge Cases)

Located in `test_bills/`:

| Number | Receipt File | Target Condition |
|---|---|---|
| 1 | `bill_01_dim_light.jpg` | Low-light ambiance with warm shadow noise |
| 2 | `bill_02_crumpled.jpg` | Folded, crumpled paper with crease artifacts |
| 3 | `bill_03_steep_angle.jpg` | 40-degree perspective tilt and trapezoidal keystone distortion |
| 4 | `bill_04_faded_thermal.jpg` | Faded thermal substrate with low dot-matrix contrast |
| 5 | `bill_05_handwritten.jpg` | Manual pen-and-paper cursive handwriting |
| 6 | `bill_06_two_scripts.jpg` | Bilingual Devanagari (Hindi) and English line items |
| 7 | `bill_07_long_bill_p1 & p2` | Multi-panel banquet invoice across sequential captures |
| 8 | `bill_08_wrong_printed_total.jpg` | Faulty printed receipt total (+42.50 cashier arithmetic discrepancy) |
| 9 | `bill_09_family_feast.jpg` | Multi-person feast with shared dishes |
| 10 | `bill_10_cafe_discounts.jpg` | Promotional coupon deduction combined with service fee |
| 11 | `bill_11_brewery_vat.jpg` | Dual tax structure: State alcohol VAT (10%) and Food GST (5%) |
| 12 | `bill_12_party_night.jpg` | Large gathering tab with 10% service charge |

---

## Installation and Execution

### 1. Clone Repository
```bash
git clone https://github.com/Milee-Goyal/Split_The_Bill.git
cd Split_The_Bill
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Launch Server
Using Python:
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Or on Windows, double-click `run_app.bat`.

Open: `http://localhost:8000`

---

## Automated Test Suite

Execute the test suite (Pydantic schema validation, proportional allocation, rounding reconciliation, and API integration):

```bash
python -m pytest -v
```

Output:
```
tests/test_api.py::test_list_sample_bills_endpoint PASSED
tests/test_api.py::test_get_bill_detail_endpoint PASSED
tests/test_api.py::test_calculate_endpoint_api PASSED
tests/test_calculator.py::test_proportional_tax_split_not_equal PASSED
tests/test_calculator.py::test_shared_all_items PASSED
tests/test_calculator.py::test_discrepancy_detection_on_wrong_total PASSED
tests/test_ground_truth.py::test_ground_truth_contains_at_least_12_bills PASSED
tests/test_ground_truth.py::test_ground_truth_pydantic_validation PASSED
tests/test_ground_truth.py::test_bill_08_identifies_wrong_printed_total PASSED
tests/test_ground_truth.py::test_dim_light_and_faded_thermal_have_lower_confidences PASSED

============================== 10 passed in 0.38s ==============================
```
