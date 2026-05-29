# TAA AI-Powered Perishable Demand Forecasting System

**Route:** DMK → MLE → DMK | **Last Updated:** 2026-05-29

AI-driven Buy-on-Board (BoB) perishable inventory optimization for Thai AirAsia's DMK–MLE–DMK route. Replaces manual stocking heuristics that produced a simultaneous **23–34% sell-through rate** and **12–20% stockout rate** in early 2026 — discarding 65–76% of loaded food while still running out of best-sellers.

The system outputs **Q\* (optimal load quantity)** per product per flight, derived from a 7-theory operations research pipeline.

---

## Core Design Principle

The **pair route (DMK→MLE→DMK)** is the single atomic unit of every decision. All catering is loaded at DMK hub; no replenishment occurs at MLE. All perishable inventory must be disposed of at DMK on the return leg. This makes the round trip — not each individual leg — the correct planning unit.

---

## System Architecture

| Component | File | Purpose |
| :--- | :--- | :--- |
| **Backend** | `app.py` | Flask REST API — 7-theory pipeline, Tobit MLE, Newsvendor Q* |
| **Dashboard** | `forecast_app.html` | 3-tab interactive web dashboard |
| **Menu state** | `active_menu.json` | Persistent active/inactive product list with prices and costs |
| **Historical data** | `<DATA_DIR>/` | SaleALL, Wastage, PAX, PBM, and Cost Perishable CSVs |
| **Uploads** | `uploads/` | Per-flight passenger manifest + PBM files |
| **Actuals** | `uploads/actuals/` | Post-flight sales + wastage for Theory 7 MLE refit |

### Requirements

```
Python 3.9+
flask
numpy
pandas
scipy
```

Install dependencies:
```bash
pip install flask numpy pandas scipy
```

### How to Run

1. Set `DATA_DIR` in `app.py` to the folder containing your historical CSV files.
2. Start the server:

```bash
python app.py
```

3. Open **http://127.0.0.1:5000** in your browser.

---

## Training Data Inventory (as of 2026-05-24)

| Category | File | Period | Rows |
| :--- | :--- | :--- | ---: |
| **Sales** | SaleALL2024.csv | Full year 2024 | 70,932 |
| | SaleALL2025.csv | Full year 2025 | 76,516 |
| | SaleALL2026_Month1_4.csv | Jan – Apr 2026 | 25,378 |
| | SaleALL2026_Month5_24.csv | May 1–24, 2026 | 4,347 |
| | ***Sales subtotal*** | | ***177,173*** |
| **PAX** | Passenger_Nat_Age_Seat-2024.csv | Full year 2024 | 106,433 |
| | Passenger_Nat_Age_Seat-2025.csv | Full year 2025 | 99,072 |
| | Passenger_Nat_Age_Seat-2026_Month5_24.csv | Jan – May 24, 2026 | 43,247 |
| | ***PAX subtotal*** | | ***248,752*** |
| **PBM** | PBM-DATA_2024.csv | Full year 2024 | 60,944 |
| | PBM-DATA_2025.csv | Full year 2025 | 51,523 |
| | PBM-DATA_2026_Month1_4.csv | Jan – Apr 2026 | 22,842 |
| | PBM-DATA_2026_Month5_24.csv | May 1–24, 2026 | 4,023 |
| | ***PBM subtotal*** | | ***139,332*** |
| **Wastage** | Wastage-2024.csv | Full year 2024 | 3,921 |
| | Wastage-2025.csv | Full year 2025 | 3,897 |
| | Wastage-2026_Month1_4.csv | Jan – Apr 2026 | 1,596 |
| | Wastage-2026_Month5_24.csv | May 1–24, 2026 | 237 |
| | ***Wastage subtotal*** | | ***9,651*** |
| **Reference** | Cost Perishable.csv | SKU cost & price | 49 |
| | **Grand Total** | | **574,957** |

> The 2026 PAX file uses a cumulative naming convention — `Month5_24` covers all flights from January through May 24, 2026.

---

## The 7-Theory Pipeline

| # | Theory | Role | Status |
| :---: | :--- | :--- | :---: |
| T1 | **Pair-Route Aggregation** | Sums S1+S2 sales per date → eliminates crew misattribution error | Active |
| T2 | **Demand Censoring (Monthly Rate Tobit MLE)** | Fits Tobit on per-pax demand rate (units/net\_bob) per calendar month using 2024–2026 history; outputs μ\_rate and σ\_rate per month | Active |
| T3 | **Newsvendor Model** | Defines C\_u (underage cost) and C\_o (overage cost) | Active |
| T4 | **Critical Fractile** | Derives target service level F\* = C\_u / (C\_u + C\_o); computes z-score buffer | Active |
| T5 | **Flight-Specific Scaling** | Q\* = μ\_rate × net\_bob + z × σ\_rate × net\_bob; net\_bob from uploaded manifest | Requires upload |
| T5b | **Demographic Gamma (A1)** | γ per SKU = upcoming nationality-weighted rate ÷ historical month nationality-weighted rate | Active when manifest has nationality data |
| T6 | **Product Substitution** | Cold-start baseline for new menu items using a proxy SKU's μ\_rate/σ\_rate | Active (new items only) |
| T7 | **MLE Refit** | Re-runs full Tobit MLE on historical + actuals after post-flight upload | Triggered via `/api/actuals` |

---

## REST API Endpoints

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/` | GET | Serve dashboard HTML |
| `/api/menu` | GET | Load active perishable menu |
| `/api/menu/toggle` | POST | Toggle item active/inactive |
| `/api/menu/add` | POST | Add new seasonal item (Theory 6 cold start) |
| `/api/upload` | POST | Upload passenger manifest + PBM CSV; returns demographics, duplicate warning, date mismatch error |
| `/api/forecast` | POST | Run full 7-theory pipeline; returns Q\* per active item |
| `/api/actuals` | POST | Upload post-flight actual sales + wastage; triggers Theory 7 MLE refit |
| `/api/daily-sales` | GET | Return per-day perishable sales from post-flight actuals |

---

## Data Quality Problems & Solutions

| ID | Problem | Solution |
| :---: | :--- | :--- |
| A | **Demand censoring** — stockouts hide true demand in raw sales data | Tobit MLE (T2) recovers true (μ, σ) |
| B | **Crew misattribution** — sales logged to wrong sector | Pair-route aggregation (T1) makes sector errors irrelevant |
| C | **CSV header anomaly** — FlightDate column has inconsistent casing across PSS exports | `_col()` uses case-insensitive lookup with Index-0 fallback |
| D | **Wastage column flaw** — `open_quantity - sale_quantity` only subtracts outbound sales, inflating spoilage | `open_quantity` used only as censoring cap; wastage column ignored |
| E | **Theory 5 PBM inflation** *(Fixed 2026-05-29)* | `D_0 = mu / total_pax` — normalises against total pax |
| F | **net\_bob date mismatch** *(Fixed 2026-05-29)* | HTTP 400 if pax and PBM files have different flight dates; files parsed in memory first, written only after validation |
| G | **Water-code denominator mismatch** *(Fixed 2026-05-29)* | `pbm_count` excludes water codes (BWFD, BWAK, BWHL, WBHL) — aligned with `_load_net_bob_history()` |

---

## Critical Ratio Reference

| Product | SKU | Price | Cost | F\* |
| :--- | :---: | :---: | :---: | :---: |
| Item 23 | `ITEM023` | 100 THB | 41 THB | 59.0% |
| Item 5 | `ITEM005` | 150 THB | 48 THB | 68.0% |
| Item 4 | `ITEM004` | 150 THB | 60 THB | 60.0% |
| Item 24 | `ITEM024` | 150 THB | 51.77 THB | 65.5% |
| Item 6 | `ITEM006` | 150 THB | 65.50 THB | 56.3% |
| Item 26 | `ITEM026` | 149 THB | 47 THB | 68.5% |
| Item 9 | `ITEM009` | 150 THB | 56 THB | 62.7% |
| Item 27 | `ITEM027` | 100 THB | 49 THB | 51.0% |

Because underage cost (lost margin) exceeds overage cost (wasted food) for all items, the optimal strategy always carries a **positive safety stock buffer** above the mean Tobit demand.

---

## Empirical Profit Optimization Results

| Product | Historical Annual Profit | Optimized Q\* Profit | Uplift |
| :--- | :---: | :---: | :---: |
| Item 23 (legacy SKU) | 197,009 THB | 239,893 THB | +21.8% |
| Item 5 | 178,942 THB | 212,458 THB | +18.7% |
| Item 4 | 98,956 THB | 152,017 THB | +53.6% |
| Item 24 | 146,913 THB | 172,034 THB | +17.1% |
| Item 1 (2025/2026 SKU) | −13,266 THB (loss) | 74,602 THB | Turnaround |

---

## Operational Workflow

### Pre-Flight (2–3 Days Before Departure)
1. Export upcoming flight's passenger manifest CSV from PSS system
2. Export PBM booking data CSV
3. Upload both in the **Forecast** tab — system detects flight date, validates both files match the same date, returns pax count, PBM count, and demographic breakdown
4. Click **Run Hyper-Personalized Forecast** — pipeline executes T1–T7, outputs Q\* per active item
5. Load catering per Q\* recommendations at DMK before departure

### Post-Flight (After Return to DMK)
1. Export actual SaleALL CSV and Wastage CSV from POS system
2. Upload in the **Post-Flight Actuals** tab
3. System saves files and re-runs Tobit MLE on full combined dataset (Theory 7 MLE refit)
4. Review updated (μ, σ, Q\*) in the results table

---

## Known Limitations

| Item | Status |
| :--- | :---: |
| Training window: 2024–2026 (~835 flight dates) | Active |
| Theory 7 is MLE refit, not true Bayesian updating | Accepted |
| Combo transactions excluded from demand model | Accepted |
| T5b γ preference weights assume uniform nationality distribution within each country | Accepted |
| T5b γ has no floor/ceiling clamp — manual Q\* override input is the operator safety valve | Intentional |
