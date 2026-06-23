# Scale-Up Design Session Summary
## TAA AI Forecasting — Expanding Beyond DMK-MLE-DMK
**Session Date:** 2026-06-17

---

## The Question
"If I want to scale up to other flights, what should we do first?"

Target route confirmed: **DMK-CNX-DMK** (Bangkok Don Mueang → Chiang Mai → Bangkok)

---

## 11 Decisions Made

### 1. Route Type: Same Hub Model (Option A)
Same pair-route operational logic applies — catering loaded at hub, no outstation replenishment, unsold food disposed on return. The Tobit/Newsvendor math does not change. Only the parameterization changes.

---

### 2. Multiple Frequencies Per Day
DMK-CNX has many frequencies per day, unlike DMK-MLE (1 frequency). Each aircraft/frequency operates independently.

---

### 3. Each Frequency Is Independent
Each aircraft on DMK-CNX gets its own separate catering cart loaded at DMK. There is no catering pooling between frequencies. Each frequency is its own inventory decision unit.

**Impact:** The current T1 aggregation by `flight_date` must become aggregation by `(flight_date, rotation_id)`. One Q* recommendation per frequency, not per day.

---

### 4. The Atomic Unit Is the ROTATION, Not the Pair
This is the most important architectural change.

Real operational patterns observed:
- `CNX → DMK → CNX` — aircraft starts at CNX, not DMK
- `HKT → BKK → CNX → HKT` — 3-leg rotation, multiple stations

A **Rotation** is defined as:
> An ordered sequence of flights starting and ending at the same **Loading Station**. The catering cart is loaded once at the Loading Station, sold throughout all legs, and all unsold inventory is disposed of when the aircraft returns to the Loading Station.

- **Net BoB (rotation-level)** = sum of `(pax − food_PBM)` across **all legs** in the rotation
- **Censoring cap** = total quantity loaded at the Loading Station (unchanged conceptually)
- **Pair Route** = a special case of Rotation with exactly 2 legs (still valid for DMK-MLE)

**Current code that must change:**
```python
PAIR_FLIGHTS = [175, 176]  # line 65 — must become rotation-aware config
```
T1 aggregation must group by `(flight_date, rotation_id)` instead of `flight_date`.

---

### 5. Rotation Structure Is Schedule-Defined, Identified by Flight Number
Rotation pairings are **fixed to the IATA season schedule** and identified by flight numbers in the PSS CSV exports. The schedule publishes two seasons per year (Summer: late March, Winter: late October). During a season, flight number → rotation mapping is stable.

**"Mostly pairs but a little unpaired":** Some flights have overnight turnarounds at CNX — the outbound departs DMK on Day N, the return arrives DMK on Day N+1. These cross-date pairs must be handled by matching on aircraft turn, not calendar date alone.

---

### 6. Rotation Config Is a Product Feature (Ops Team Manages It)
The ops team updates the rotation config through the **dashboard UI** — no developer required. This is necessary because the schedule changes twice a year (IATA seasons) and the ops team cannot wait for a code deploy.

**New product features required:**
- `routes.json` config file (managed via API + UI, not hardcoded)
- Dashboard UI: Add / Edit / Delete rotation definitions per route
- API endpoints: `GET /api/routes`, `POST /api/routes/add`, `PUT /api/routes/update`

---

### 7. Menu Is Shared, With Per-Route Activation Flags (Option A)
The physical perishable menu is the same across all routes (same SKU codes, prices, costs). However, some items are **international-only** (e.g., Nasi Lemak `FNBG03000085` is not offered on domestic DMK-CNX).

**Current `active_menu.json` schema must change:**
```json
// BEFORE (single boolean)
{ "code": "FNBG03000085", "active": true }

// AFTER (per-route activation)
{ "code": "FNBG03000085", "active": { "DMK-MLE": true, "DMK-CNX": false } }
```

All `/api/menu` endpoints (`GET`, `toggle`, `add`) must accept a `route_id` parameter.

---

### 8. Historical Data: Separate CSV Files Per Route (Option A)
AirAsia's PSS exports DMK-CNX data into its own separate CSV files, not mixed with DMK-MLE data. Training data isolation is handled at the file system level — no filtering logic required.

**New data directory structure:**
```
Desktop\AI\
  ├── (existing DMK-MLE files: SaleALL2024.csv, ...)
  └── CNX\
        ├── SaleALL_CNX_2024.csv
        ├── Passenger_CNX_2024.csv
        ├── PBM_CNX_2024.csv
        └── Wastage_CNX_2024.csv
```

Each route in `routes.json` points to its own data directory.

---

### 9. Dashboard: Single App with Route Selector (Option A)
One Flask app, one URL. A route selector (dropdown or top-level tab) at the top of the dashboard switches the entire context: active menu, rotation config, upload directories, forecast output, daily sales monitor.

**Impact on backend:**
- Every API endpoint receives a `route_id` parameter in the request
- All caches become `{route_id: value}` dicts:
  - `_pref_weights_cache` → `{route_id: {country: {sku: rate}}}`
  - `_monthly_nat_cache` → `{route_id: {month: {country: fraction}}}`
- All upload directories become `uploads/{route_id}/` and `uploads/{route_id}/actuals/`
- `MENU_FILE` logic becomes per-route activation lookup

---

## What to Build First: Ordered Build Sequence

### Step 0 — Before Writing Any Code
Collect the actual DMK-CNX rotation schedule:
- List all flight number pairs/triples in the current IATA season
- Identify any overnight turnarounds (cross-date pairs)
- Confirm which rotations start at DMK vs. CNX
- Get the DMK-CNX historical CSV files from PSS (SaleALL, PAX, PBM, Wastage)

---

### Step 1 — `routes.json` Schema (The Foundation)
Everything else is parameterized by `route_id`. Define this file first.

```json
{
  "routes": [
    {
      "id": "DMK-MLE",
      "name": "Bangkok – Maldives",
      "type": "international",
      "loading_station": "DMK",
      "data_dir": "C:\\Users\\Chaiwatwannawit\\Desktop\\AI",
      "sales_files": ["SaleALL2024.csv", "SaleALL2025.csv", ...],
      "pax_files": ["Passenger_Nat_Age_Seat-2024.csv", ...],
      "pbm_files": ["PBM-DATA_2024.csv", ...],
      "wastage_files": ["Wastage-2024.csv", ...],
      "rotations": [
        { "id": "FD175_176", "legs": [175, 176], "label": "DMK→MLE→DMK" }
      ]
    },
    {
      "id": "DMK-CNX",
      "name": "Bangkok – Chiang Mai",
      "type": "domestic",
      "loading_station": "DMK",
      "data_dir": "C:\\Users\\Chaiwatwannawit\\Desktop\\AI\\CNX",
      "sales_files": ["SaleALL_CNX_2024.csv", ...],
      "pax_files": [...],
      "pbm_files": [...],
      "wastage_files": [...],
      "rotations": [
        { "id": "FD3001_3002", "legs": [3001, 3002], "label": "DMK→CNX→DMK" },
        { "id": "FD3003_3004", "legs": [3003, 3004], "label": "DMK→CNX→DMK" }
      ]
    }
  ]
}
```

---

### Step 2 — Route-Aware API Backend
Add `route_id` to every API endpoint. Refactor all global state:

| Global (now) | Route-aware (after) |
|---|---|
| `PAIR_FLIGHTS = [175, 176]` | `routes[route_id].rotations` |
| `SALES_FILES = [...]` | `routes[route_id].sales_files` |
| `UPLOAD_DIR = uploads/` | `uploads/{route_id}/` |
| `ACTUALS_DIR = uploads/actuals/` | `uploads/{route_id}/actuals/` |
| `_pref_weights_cache` | `_pref_weights_cache[route_id]` |
| `_monthly_nat_cache` | `_monthly_nat_cache[route_id]` |

---

### Step 3 — T1 Rotation Aggregation Rewrite
Change the pair-route aggregation from "group by date, filter for flight numbers 175+176" to "group by (date, rotation_id), derive rotation_id from flight number → rotation mapping in routes.json."

This also fixes Net BoB for multi-leg rotations:
```
net_bob_rotation = sum over all legs: (leg_pax − leg_food_PBM)
```

---

### Step 4 — Menu Schema Migration
Update `active_menu.json` from flat `active: bool` to `active: {route_id: bool}`. Update `/api/menu` endpoints to accept `route_id`. The route `type` field (`domestic` / `international`) can drive default activation for new items.

---

### Step 5 — Dashboard Route Selector + Rotation Management UI
- Route dropdown at top of dashboard; all fetch calls include `route_id`
- New "Routes & Rotations" settings panel: add/edit/delete rotations per route
- Menu toggle UI becomes per-route context-aware

---

## Key Terms Resolved

| Term | Definition |
|---|---|
| **Rotation** | Atomic unit of catering. Ordered flight sequence, loaded once at Loading Station, disposed at Loading Station on return. Replaces "Pair Route" as the general case. |
| **Loading Station** | Airport where the catering cart is loaded and unsold inventory is disposed. |
| **Pair Route** | A 2-leg rotation. Special case of Rotation. DMK-MLE remains a Pair Route. |
| **Route** | Logical grouping of rotations serving the same city-pair market, sharing historical data files and menu activation profile. |
| **Route Type** | `domestic` or `international`. Determines which menu items are available (e.g., Nasi Lemak = international only). |
| **IATA Season** | One of two annual schedule periods (Summer / Winter) during which flight numbers and rotation structures are stable. |
| **Net BoB (Rotation-level)** | Sum of `(pax − food_PBM)` across all legs in a rotation. The actual market size for on-board sales. |

---

## Open Questions (Not Yet Decided)

1. **Cross-date overnight turns**: How to match outbound Day N with return Day N+1 in the rotation grouping. Need to confirm how common these are on DMK-CNX and decide whether to handle at Step 3 or defer.

2. **CNX-based rotations** (`CNX→DMK→CNX`): Treat as a separate `CNX-DMK` route with `loading_station: CNX` and its own data files? Or merge under `DMK-CNX`? Decision needed before `routes.json` is finalized.

3. **Historical data availability**: Confirm the DMK-CNX CSV files exist, cover at least 12 months, and match the expected PSS schema before committing to the build sequence.
