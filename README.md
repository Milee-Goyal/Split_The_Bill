# Split the Bill From a Photograph 🧾✨

> An AI-powered receipt OCR parser, human-in-the-loop review interface, interactive member chip assignment (Way A), and mathematically fair proportional tax & service charge calculation engine.

---

## 🚀 Key Features

1. **Photo in, Structured Bill Out (Upload & Live Camera)**:
   - **Dual Ingestion**: Users can upload existing receipt images (drag-and-drop or browse) **OR click a live photo directly with their device camera/webcam** via an interactive camera modal.
   - Parses restaurant receipts into a strict **Pydantic model** (`BillItem`, `BillTaxes`, `BillMetadata`, `ParsedBill`).
   - Extracts item descriptions, quantities, unit prices, total prices, subtotals, CGST/SGST/VAT, service charges, discounts, and grand totals.
   - Computes **per-field confidence scores** (0.0 to 1.0) based on OCR visual clarity.

2. **Human-in-the-Loop Review Screen**:
   - Displays receipt photo side-by-side with an editable data table.
   - Highlights fields where confidence is low ($<85\%$) so humans can fix OCR errors before math executes.
   - **Cashier Discrepancy Alert**: Automatically flags bills where the restaurant's printed total does not equal $\text{items} + \text{tax} - \text{discount}$.

3. **Interactive Member Chips Assignment (Way A)**:
   - Dynamic friend participant tags with colorful avatars.
   - Interactive toggle chips on every food item: click member chips or `[Everyone]` to distribute.
   - **Real-time Live Spend Ticker**: Shows live balances as chips are toggled.

4. **Mathematically Fair Proportional Splitting**:
   - Eliminates the unfair "equal tax split" bug. Taxes and service charges distribute **in strict proportion to each person's food spend fraction** ($S_i / S_{\text{total}}$).
   - Exact penny/paise reconciliation ensures $\sum \text{Member Totals} \equiv \text{Bill Grand Total}$ without rounding loss.

5. **12 Challenging Real-World Test Receipts**:
   - Includes full dataset with synthetic/transformed receipts and hand-labeled ground truth in `test_bills/ground_truth.json`.

---

## 📊 Proportional Fair-Share Math Formula

### The Problem with Naive Splitting:
Suppose two friends eat dinner:
- **Rahul** eats ₹700 of food.
- **Amit** only drinks a ₹100 juice.
- Subtotal = ₹800. Restaurant GST (5%) + Service Fee (10%) = ₹120. Total = ₹920.

* **Naive (Unfair) Way**: Split ₹120 fees equally $\rightarrow$ ₹60 each. Amit pays ₹160 (60% tax rate on his ₹100 drink!).
* **Our Proportional (Fair) Engine**:
  $$\text{Spend Fraction } r_i = \frac{\text{Personal Food Subtotal } S_i}{\text{Total Food Subtotal } S_{\text{total}}}$$
  $$\text{Fair Tax \& Fees Share } T_i = \text{Total Taxes} \times r_i$$
  - Amit's fraction: $100 / 800 = 12.5\% \rightarrow \text{Tax \& Fee} = 120 \times 0.125 = ₹15.00$.
  - Rahul's fraction: $700 / 800 = 87.5\% \rightarrow \text{Tax \& Fee} = 120 \times 0.875 = ₹105.00$.
  - **Amit pays ₹115.00, Rahul pays ₹805.00.** Total matches ₹920.00 to the penny.

---

## 🔍 What is Mocked vs. What is Live?

To make this repository **100% reproducible out-of-the-box without requiring paid API keys**:
* **Live Vision AI (Optional)**: If you supply `GEMINI_API_KEY` or `OPENAI_API_KEY` in your environment, `/api/upload` will invoke `gemini-1.5-flash` or `gpt-4o` multimodal vision models.
* **Offline Mock & Ground-Truth Test Suite (Default)**: Pre-loaded with 12 challenging edge-case receipts and hand-annotated ground truths in `test_bills/ground_truth.json`. Clicking any sample loads the authentic data with realistic OCR confidence scores and image previews instantly.
* **Deterministic Logic (Always Live)**: The Pydantic validation, discrepancy detector, interactive chip assignment UI, and proportional math calculation engine are **100% real, active production code**.

---

## 📁 12 Test Cases (Challenging Conditions)

All 12 test conditions from the problem brief are implemented in `test_bills/`:

| # | Test Bill File | Real-World Hard Condition |
|---|---|---|
| 1 | `bill_01_dim_light.jpg` | Low lighting ambiance with warm restaurant shadow noise |
| 2 | `bill_02_crumpled.jpg` | Folded, crumpled paper with crease line artifacts |
| 3 | `bill_03_steep_angle.jpg` | 40-degree perspective tilt & trapezoid keystone distortion |
| 4 | `bill_04_faded_thermal.jpg` | Faded thermal print with low contrast dot-matrix letters |
| 5 | `bill_05_handwritten.jpg` | Pen & paper cursive handwriting from traditional dhaba |
| 6 | `bill_06_two_scripts.jpg` | Bilingual Devanagari (Hindi) + English script line items |
| 7 | `bill_07_long_bill_p1 & p2` | Multi-panel tall banquet invoice stitched across pages |
| 8 | `bill_08_wrong_printed_total.jpg` | **Genuinely faulty printed total** (cashier arithmetic mismatch) |
| 9 | `bill_09_family_feast.jpg` | Multi-person feast with shared gravies and bread units |
| 10 | `bill_10_cafe_discounts.jpg` | Promotional 10% coupon deduction + service fee |
| 11 | `bill_11_brewery_vat.jpg` | Dual tax structure: State alcohol VAT (10%) + Food GST (5%) |
| 12 | `bill_12_party_night.jpg` | Large table tab with 10% service charge and mixed courses |

---

## 🛠️ Quickstart Installation & Running

### 1. Clone & Enter Directory
```bash
git clone <your-repo-url>
cd "Split the Bill From a Photograph"
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Start the Application
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Open your browser and navigate to: **`http://localhost:8000`**

---

## 🧪 Running Automated Tests

Run the full automated test suite (Pydantic schema validation, proportional tax logic, penny reconciliation, and API endpoints):

```bash
python -m pytest
```

Output:
```
============================== 10 passed in 0.47s ==============================
```

---

## 📹 90-Second Demo Video Guide (For Placement Submission)

When recording your demo video to post on Google Drive:
1. **0:00 - 0:15 (Upload & Gallery)**: Show the landing page in **Light Mode**. Point out the 12 pre-loaded challenging receipt edge cases. Click on `bill_08_wrong_printed_total` or `bill_01_dim_light`.
2. **0:15 - 0:35 (Review Screen)**: Show the side-by-side view. Highlight the receipt photo on the left, the editable table on the right, the **OCR Confidence badges** (Green/Amber), and point out the **Discrepancy Banner** detecting the cashier's math mistake!
3. **0:35 - 0:55 (Interactive Member Chips)**: Click *Continue to Member Chips*. Show members (`Rahul`, `Priya`, `Amit`). Click member chips on dishes (e.g. Biryani $\rightarrow$ Rahul & Priya; Coke $\rightarrow$ Amit). Show the **Live Spend Ticker** updating in real time.
4. **0:55 - 1:20 (Fair-Share Breakdown)**: Click *Calculate Proportional Split*. Show the member cards, the exact proportional tax formula, and the *"Exact Penny Match"* badge.
5. **1:20 - 1:30 (WhatsApp Export)**: Click *"Copy Summary for WhatsApp / UPI"* and show the formatted text.
