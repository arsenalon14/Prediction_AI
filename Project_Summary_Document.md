# Project Summary Document
## TAA AI-Powered Perishable Demand Forecasting System
**Route:** DMK → MLE → DMK | **Last Updated:** 2026-05-29 (rev 2)

---

## 1. Project Overview

This system provides AI-driven Buy-on-Board (BoB) perishable inventory optimization for Thai AirAsia's DMK–MLE–DMK route. It replaces manual stocking heuristics that produced a simultaneous **23–34% sell-through rate** and **12–20% stockout rate** in early 2026 — discarding 65–76% of loaded food while still running out of best-sellers.

The system outputs **Q* (optimal load quantity)** per product per flight, derived from a 7-theory operations research pipeline.

---

## 2. Core Design Principle

The **pair route (DMK→MLE→DMK)** is the single atomic unit of every decision. All catering is loaded at DMK hub; no replenishment occurs at MLE. All perishable inventory must be disposed of at DMK on the return leg. This makes the round trip — not each individual leg — the correct planning unit.

---

## 3. System Architecture

| Component | File | Purpose |
| :--- | :--- | :--- |
| **Backend** | `app.py` | Flask REST API — 7-theory pipeline, Tobit MLE, Newsvendor Q* |
| **Dashboard** | `forecast_app.html` | 3-tab interactive web dashboard |
| **Menu state** | `active_menu.json` | Persistent active/inactive product list with prices and costs |
| **Historical data** | `C:\Users\Chaiwatwannawit\Desktop\AI\` | SaleALL, Wastage, Cost Perishable CSVs |
| **Uploads** | `uploads/` | Per-flight pax + PBM manifests |
| **Actuals** | `uploads/actuals/` | Post-flight sales + wastage for Theory 7 MLE refit |

### How to Run
```
cd C:\Users\Chaiwatwannawit\Desktop\AGY
python app.py
```
Open browser at **http://127.0.0.1:5000**

---

## 3.1. Training Data Inventory (as of 2026-05-24)

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
| | | | |
| | **Grand Total** | | **574,957** |

---

## 4. The 7-Theory Pipeline

| # | Theory | Role | Status |
| :---: | :--- | :--- | :---: |
| T1 | **Pair-Route Aggregation** | Sums S1+S2 sales per date → eliminates crew misattribution error | Active |
| T2 | **Demand Censoring (Monthly Rate Tobit MLE)** | Fits Tobit on per-pax demand rate (units/net_bob) per calendar month using 2024–2026 history; outputs μ_rate and σ_rate per month | Active |
| T3 | **Newsvendor Model** | Defines C_u (underage cost) and C_o (overage cost) | Active |
| T4 | **Critical Fractile** | Derives target service level F* = C_u / (C_u + C_o); computes z-score buffer | Active |
| T5 | **Flight-Specific Scaling** | Q* = μ_rate × net_bob_up + z × σ_rate × net_bob_up; net_bob_up from uploaded manifest | **Requires upload** (blocks without it) |
| T5b | **Demographic Gamma (A1)** | γ per SKU = upcoming_nationality_weighted_rate ÷ historical_month_nationality_weighted_rate; preference weights from PAX×sales seat join; Q*_adjusted = γ × Q*_baseline | Active when manifest has nationality data |
| T6 | **Product Substitution** | Cold-start baseline for new menu items using a proxy SKU's μ_rate/σ_rate | Active (new items only) |
| T7 | **MLE Refit** | Re-runs full Tobit MLE on historical + actuals after post-flight upload | Triggered via `/api/actuals` |

---

## 5. REST API Endpoints

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/` | GET | Serve dashboard HTML |
| `/api/menu` | GET | Load active perishable menu |
| `/api/menu/toggle` | POST | Toggle item active/inactive |
| `/api/menu/add` | POST | Add new seasonal item (Theory 6 cold start) |
| `/api/upload` | POST | Upload passenger manifest + PBM CSV; returns demographics, duplicate warning, date mismatch error |
| `/api/forecast` | POST | Run full 7-theory pipeline; returns Q* per active item |
| `/api/actuals` | POST | Upload post-flight actual sales + wastage; triggers Theory 7 MLE refit |
| `/api/daily-sales` | GET | Return per-day perishable sales from post-flight actuals only |

---

## 6. Data Quality Problems & Solutions

| ID | Problem | Solution |
| :---: | :--- | :--- |
| A | **Demand censoring** — stockouts hide true demand in raw sales data | Tobit MLE (T2) recovers true (μ, σ) |
| B | **Crew misattribution** — sales logged to wrong sector | Pair-route aggregation (T1) makes sector errors irrelevant |
| C | **CSV header anomaly** — FlightDate column has inconsistent casing across PSS exports | `_col()` uses case-insensitive lookup with Index-0 fallback; `[WARN]` printed if fallback triggers |
| D | **Wastage column flaw** — `open_quantity - sale_quantity` only subtracts outbound sales, inflating spoilage | `wastage` column never used; `open_quantity` used only as censoring cap |
| E | **Theory 5 PBM inflation** — `D_0 = mu / N_active` with `ages` summing to `total_pax` inflated Q* by the PBM ratio *(FIXED 2026-05-29)* | `D_0 = mu / total_pax` — normalises against total pax; scaling is pure demographic mix |
| F | **net_bob date mismatch** — subtracting PBM rows from pax rows with no date validation *(FIXED 2026-05-29)* | HTTP 400 returned if pax and PBM files have different extracted flight dates; **rev 2:** files now parsed into memory first, validated, then saved — no orphan files on mismatch |
| G | **Water-code denominator mismatch** — `pbm_count = len(df)` counted all PBM rows including water codes (BWFD, BWAK, BWHL, WBHL); historical training excluded them; 37.6% of 139,332 PBM rows are water codes → 8–11% systematic Q* underestimation *(FIXED 2026-05-29 rev 2)* | `pbm_count = (~df[ssr_col].isin(WATER_CODES)).sum()` — food-only PBMs, aligned with `_load_net_bob_history()` |

---

## 7. Critical Ratio Reference (Newsvendor Financial Parameters)

| Product | SKU | Price | Cost | Critical Ratio (F*) |
| :--- | :---: | :---: | :---: | :---: |
| Boba Thai Milk Tea | `FNBG02000276` | 100 THB | 41 THB | 59.0% |
| ML NOI Fried Chicken Basil | `FNBG03000041` | 150 THB | 48 THB | 68.0% |
| Uncle Chin Chicken Rice | `FNBG03000025` | 150 THB | 60 THB | 60.0% |
| Chicken Teriyaki with Rice | `FNBG03000027` | 150 THB | 51.77 THB | 65.5% |
| Nasi Lemak | `FNBG03000085` | 150 THB | 65.50 THB | 56.3% |
| Green Curry Chicken & Egg | `FNBG03001956` | 149 THB | 47 THB | 68.5% |
| Palmyra Somtam Chicken | `FNBG03002061` | 150 THB | 56 THB | 62.7% |
| The OG Burnt Cheesecake | `FNBG03002010` | 100 THB | 49 THB | 51.0% |

**Key insight:** Because underage cost (lost margin) exceeds overage cost (wasted food) for all items, the optimal strategy always carries a **positive safety stock buffer** above the mean Tobit demand.

---

## 8. Empirical Profit Optimization Results (Tobit vs. Historical Heuristics)

| Product | Historical Annual Profit | Optimized Q* Profit | Uplift |
| :--- | :---: | :---: | :---: |
| Boba Thai Milk Tea (legacy SKU) | 197,009 THB | 239,893 THB | +21.8% |
| ML NOI Fried Chicken Basil | 178,942 THB | 212,458 THB | +18.7% |
| Uncle Chin Chicken Rice | 98,956 THB | 152,017 THB | +53.6% |
| Chicken Teriyaki with Rice | 146,913 THB | 172,034 THB | +17.1% |
| Boba Milk Tea (2025/2026 SKU) | −13,266 THB (loss) | 74,602 THB | Turnaround |

---

## 9. Operational Workflow

### Pre-Flight (2–3 Days Before Departure)
1. Export upcoming flight's passenger manifest CSV from PSS system
2. Export PBM booking data CSV
3. Upload both in the **Forecast** tab — system detects flight date, validates both files match the same date, returns pax count, PBM count, and demographic breakdown
4. Click **Run Hyper-Personalized Forecast** — pipeline executes T1–T7, outputs Q* per active item
5. Load catering per Q* recommendations at DMK before departure

### Post-Flight (After Return to DMK)
1. Export actual SaleALL CSV and Wastage CSV from POS system
2. Upload in the **Post-Flight Actuals** tab
3. System saves files to `uploads/actuals/` and re-runs Tobit MLE on full combined dataset (Theory 7 MLE refit)
4. Review updated (μ, σ, Q*) in the Bayesian update table

---

## 10. Known Limitations & Pending Items

| Item | Status | Notes |
| :--- | :---: | :--- |
| Training data window: 2024–2026 (2.5 years, ~835 flight dates) | Active | Historical CSVs for 2024, 2025, and 2026 (Jan 1 – May 24) are all fed into `app.py`. `Passenger_Nat_Age_Seat-2026_Month5_24.csv` covers the full Jan–May 2026 period. Tobit fitted on per-pax demand rates per calendar month. Discontinued items absent from their period naturally produce no monthly_params entry — model falls back to global rate. |
| Theory 7 is MLE refit, not true Bayesian updating | Accepted | Label corrected. With 140+ historical records, MLE ≈ Bayesian (flat prior). Revisit if model is deployed on shorter windows. |
| `tobit_uncensoring.py` uses a different algorithm (grid-search) from `app.py` (Nelder-Mead) | Open | The standalone script reads `perishable_historical_data.csv`; `app.py` reads 2026 CSVs directly. Results differ. Unify if a single canonical model is needed. |
| Combo transactions excluded from demand | Accepted | `new_product_category = 'Combo'` rows are filtered out. Only standalone `Perishable` rows feed demand. Decision confirmed intentional. |
| T5b γ preference weights assume nationality distribution is uniform within each country | Accepted | Preference weight = total_units_sold_to_nationality / total_pax_of_nationality across all 2024–2026 dates. Intra-nationality variation (e.g. first-time vs. repeat Chinese tourists) is not modeled. |
| T5b γ has no floor/ceiling clamp | Intentional | Extreme deviations (e.g. 0% Chinese in July → γ ≈ 0.4 for Teriyaki) are valid. Manual override input in the Adjusted Q* column is the operator safety valve. |
| `_pref_weights_cache` and `_monthly_nat_cache` survive server restarts but reset on `/api/actuals` | Active | Preference weights are invalidated after each post-flight actuals upload (T7 refit) so new sales data is incorporated on the next forecast. Monthly nat fracs (from PAX files only) are never invalidated — they are stable. |

---

## 11. Code Review History

| Date | Reviewer | Scope | Outcome |
| :---: | :--- | :--- | :--- |
| 2026-05-29 | Claude Code (`/scrutinize` + `/karpathy-guidelines`) | Full `app.py` + `forecast_app.html` | 7 issues found and fixed (see Section 6, Problems E–F; `app.py` and `forecast_app.html` updated). All fixes verified via `test_api.py` — 4/4 endpoints passed. |
| 2026-05-29 | Claude Code (`/karpathy-guidelines` Option B) | Full model redesign | Rewrote `run_pipeline()`: Tobit now fits per-pax demand rate per calendar month (T2-Rate) using 2024–2026 history (835 dates). T5 changed from demographic multiplier to `Q* = μ_rate × net_bob_up`. `/api/forecast` blocks (HTTP 400) without uploaded manifest. Forecast button disabled until upload succeeds. Discontinued items handled naturally (absent months → global rate fallback). Verified via `test_api.py` — 400 without manifest (PASS), 200 with mock demographics returning 10 active items with sensible Q* values. |
| 2026-05-29 rev 2 | Claude Code (`/scrutinize recheck`) | Full `app.py` + `forecast_app.html` post-redesign | 7 findings fixed: **(Blocker)** Problem G — water-code denominator mismatch causing 8–11% Q* underestimation on every forecast; **(Major)** file writes deferred until after date validation (no orphan files); **(Major)** `runForecast()` in HTML now checks `res.ok` — server errors no longer silently crash as TypeErrors; **(Moderate)** T7 theory tag now conditional on actuals existing in `ACTUALS_DIR`; **(Moderate)** stale "Bayesian update" label corrected to "MLE Refit" in HTML; **(Moderate)** `_load_sales()`/`_load_wastage()` docstrings corrected from "2026" to "2024–2026"; **(Nit)** add-item form now surfaces 409 Conflict via `alert()` instead of silently closing modal. |
| 2026-05-29 rev 3 | Claude Code (A1 demographic override) | `app.py` + `forecast_app.html` | **T5b Demographic Gamma (A1) implemented.** Three new helpers added to `app.py`: `_build_preference_weights()` (seat-joins PAX×sales to derive nationality→SKU purchase rates; cached), `_get_monthly_nat_fracs(month)` (historical nationality composition per calendar month; cached), `_compute_gamma(nat_counts, month, sku_codes)` (γ per SKU = upcoming weighted rate ÷ historical month weighted rate). `run_pipeline()` pre-computes gammas before the item loop; `q_adjusted = ceil(q_baseline × γ)`; `delta = q_adjusted − q_baseline`; `gamma` field added to each result. `upload_csv()` nationality bucketing changed from TH/international to top-5 actual country names + "Others". `post_flight_actuals()` invalidates `_pref_weights_cache`. Frontend: nationality pills displayed after upload; Adjusted Q* column is now an editable number input (manual operator override); δ badge updates live on keypress; γ tag shown when |γ−1| > 0.01. |
