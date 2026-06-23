"""
IFS-AI Perishable Demand Forecasting Server
============================================
7-Theory Pipeline:
  1. Pair-Route Aggregation (flights 175+176)
  2. Demand Censoring (Tobit MLE)
  3. Newsvendor Model (C_o, C_u)
  4. Critical Fractile (Q* baseline)
  5. Load Factor / Demographics
  6. Product Substitution (cold start)
  7. MLE Refit (triggered by post-flight actuals upload via /api/actuals)
"""

import json, math, os, sys, warnings
from pathlib import Path

# Ensure stdout can handle Unicode (Greek γ, Thai chars) on Windows cp1252 consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_file
from scipy.optimize import minimize
from scipy.stats import norm

warnings.filterwarnings("ignore")

# ── paths ────────────────────────────────────────────────────────────────
BASE_DIR   = Path(r"C:\Users\Chaiwatwannawit\Desktop\AGY")
DATA_DIR   = Path(r"C:\Users\Chaiwatwannawit\Desktop\AI")
HTML_FILE  = BASE_DIR / "forecast_app.html"
MENU_FILE  = BASE_DIR / "active_menu.json"
ROUTES_FILE = BASE_DIR / "routes.json"
SCHEDULE_FILE = BASE_DIR / "schedule.csv"
UPLOAD_DIR  = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ACTUALS_DIR = UPLOAD_DIR / "actuals"
ACTUALS_DIR.mkdir(exist_ok=True)

COST_FILE     = DATA_DIR / "Cost Perishable.csv"
WATER_CODES   = {"BWFD", "BWAK", "BWHL", "WBHL"}
RECENCY_WEIGHT_FACTOR = 10.0  # Weight factor for post-flight actuals to adapt to recent structural changes

SALES_FILES = [
    DATA_DIR / "SaleALL2024.csv",
    DATA_DIR / "SaleALL2025.csv",
    DATA_DIR / "SaleALL2026_Month1_4.csv",
    DATA_DIR / "SaleALL2026_Month5_24.csv",
]
WASTAGE_FILES = [
    DATA_DIR / "Wastage-2024.csv",
    DATA_DIR / "Wastage-2025.csv",
    DATA_DIR / "Wastage-2026_Month1_4.csv",
    DATA_DIR / "Wastage-2026_Month5_24.csv",
]
PAX_FILES = [
    DATA_DIR / "Passenger_Nat_Age_Seat-2024.csv",
    DATA_DIR / "Passenger_Nat_Age_Seat-2025.csv",
    DATA_DIR / "Passenger_Nat_Age_Seat-2026_Month5_26.csv",
]
PBM_FILES = [
    DATA_DIR / "PBM-DATA_2024.csv",
    DATA_DIR / "PBM-DATA_2025.csv",
    DATA_DIR / "PBM-DATA_2026_Month1_4.csv",
    DATA_DIR / "PBM-DATA_2026_Month5_26.csv",
]
PAIR_FLIGHTS = {175, 176, "175", "176"}

# Dynamic Configurations
def _load_routes_config():
    if ROUTES_FILE.exists():
        try:
            with open(ROUTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)["routes"]
        except Exception as e:
            print(f"[ERROR] Failed to read routes.json: {e}")
    return []

def _load_schedule_config():
    if SCHEDULE_FILE.exists():
        try:
            return pd.read_csv(SCHEDULE_FILE)
        except Exception as e:
            print(f"[ERROR] Failed to read schedule.csv: {e}")
    return pd.DataFrame(columns=["route_id", "rotation_id", "start_date", "end_date", "flight_num", "day_offset", "loading_station"])

def _resolve_flight_col(df):
    """Find flight number column case-insensitively."""
    low_map = {c.lower().strip(): c for c in df.columns}
    for k in ["flightnumber", "flightnum", "flight_num", "flightno", "flight"]:
        if k in low_map:
            return low_map[k]
    # Fallback to column with "flight" in it
    for c in df.columns:
        if "flight" in c.lower():
            return c
    return df.columns[0]

def _apply_schedule_mapping_to_df(df, flight_col=None, date_col=None):
    """
    Vectorized-friendly approach to enrich a DataFrame with schedule information.
    Adds: route_id, rotation_id, day_offset, loading_station, rotation_date
    """
    if df.empty:
        df["route_id"] = None
        df["rotation_id"] = None
        df["day_offset"] = 0
        df["loading_station"] = None
        df["rotation_date"] = None
        return df

    if not flight_col:
        flight_col = _resolve_flight_col(df)
    if not date_col:
        date_col = _col(df, "flightdate")
        
    sched_df = _load_schedule_config()
    if sched_df.empty:
        df["route_id"] = None
        df["rotation_id"] = None
        df["day_offset"] = 0
        df["loading_station"] = None
        df["rotation_date"] = df[date_col]
        return df

    df = df.copy()
    # Create key for matching: flight_num as int
    df["_flight_num_int"] = pd.to_numeric(df[flight_col], errors="coerce").fillna(-1).astype(int)
    # Convert dates to datetime objects
    df["_date_dt"] = pd.to_datetime(df[date_col], errors="coerce")
    
    # Prepare schedule rows with datetime boundaries
    sched_records = []
    for _, row in sched_df.iterrows():
        try:
            sched_records.append({
                "flight_num": int(row["flight_num"]),
                "route_id": row["route_id"],
                "rotation_id": row["rotation_id"],
                "start_dt": pd.to_datetime(row["start_date"]),
                "end_dt": pd.to_datetime(row["end_date"]),
                "day_offset": int(row["day_offset"]),
                "loading_station": row["loading_station"]
            })
        except Exception:
            continue
            
    # We will build mapping arrays
    route_ids = [None] * len(df)
    rotation_ids = [None] * len(df)
    day_offsets = [0] * len(df)
    loading_stations = [None] * len(df)
    rotation_dates = [None] * len(df)
    
    # Convert dataframe columns to list for faster iteration
    flight_nums = df["_flight_num_int"].tolist()
    dates_dt = df["_date_dt"].tolist()
    dates_orig = df[date_col].tolist()
    
    # Cache schedule records by flight_num for speed O(1) flight lookup
    sched_by_flight = {}
    for r in sched_records:
        sched_by_flight.setdefault(r["flight_num"], []).append(r)
        
    for i in range(len(df)):
        f_num = flight_nums[i]
        f_dt = dates_dt[i]
        
        if f_num == -1 or pd.isna(f_dt):
            rotation_dates[i] = dates_orig[i]
            continue
            
        matched = False
        if f_num in sched_by_flight:
            for r in sched_by_flight[f_num]:
                if r["start_dt"] <= f_dt <= r["end_dt"]:
                    route_ids[i] = r["route_id"]
                    rotation_ids[i] = r["rotation_id"]
                    day_offsets[i] = r["day_offset"]
                    loading_stations[i] = r["loading_station"]
                    rotation_dates[i] = (f_dt - pd.Timedelta(days=r["day_offset"])).strftime("%Y-%m-%d")
                    matched = True
                    break
        if not matched:
            rotation_dates[i] = f_dt.strftime("%Y-%m-%d") if not pd.isna(f_dt) else dates_orig[i]
            
    df["route_id"] = route_ids
    df["rotation_id"] = rotation_ids
    df["day_offset"] = day_offsets
    df["loading_station"] = loading_stations
    df["rotation_date"] = rotation_dates
    
    # Cleanup temporary columns
    df = df.drop(columns=["_flight_num_int", "_date_dt"])
    return df

# Module-level caches — populated lazily, invalidated when actuals arrive
_pref_weights_cache = {}   # {route_id: {country: {sku: avg_units_per_pax}}}
_monthly_nat_cache  = {}   # {route_id: {month_int: {country: fraction}}}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# ══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _col(df, name):
    """Case-insensitive column lookup with Index-0 fallback."""
    low = {c.lower().strip(): c for c in df.columns}
    if name.lower() in low:
        return low[name.lower()]
    print(f"[WARN] _col: '{name}' not found in columns — falling back to column 0 ({df.columns[0]!r})")
    return df.columns[0]


def _expected_sales(Q, mu, sigma):
    """Compute expected sales of loading Q units given N(mu, sigma^2) demand."""
    if Q <= 0:
        return 0.0
    if sigma < 1e-4:
        return float(min(mu, Q))
    z = (Q - mu) / sigma
    phi = norm.pdf(z)
    Phi = norm.cdf(z)
    loss = phi - z * (1.0 - Phi)
    exp_sales = mu - sigma * loss
    return float(max(0.0, exp_sales))


def _expected_profit(Q, mu, sigma, price, cost):
    """Compute expected financial profit of loading Q units."""
    exp_sales = _expected_sales(Q, mu, sigma)
    return float(price * exp_sales - cost * Q)



def _extract_flight_date(df):
    """Read FlightDate from first column (case-insensitive, Index-0 fallback)."""
    synonyms = {"flightdate", "date", "flight_date", "flight date"}
    low = {c.lower().strip(): c for c in df.columns}
    col = None
    for syn in synonyms:
        if syn in low:
            col = low[syn]
            break
    if col is None:
        col = df.columns[0]
    raw = df[col].dropna()
    if raw.empty:
        return None
    try:
        parsed = pd.to_datetime(raw, errors="coerce").dropna()
        if not parsed.empty:
            return parsed.mode().iloc[0].strftime("%Y-%m-%d")
    except Exception:
        pass
    return str(raw.mode().iloc[0]) if not raw.empty else None


def _load_cost_map():
    """Return {code: unit_cost} using latest available year."""
    df = pd.read_csv(COST_FILE)
    cost_map = {}
    for _, row in df.iterrows():
        code = str(row["Code"]).strip()
        # prefer 2026, then 2025, then 2024
        for yr in ["2026", "2025", "2024"]:
            if yr in df.columns and pd.notna(row.get(yr)):
                cost_map[code] = float(row[yr])
                break
    return cost_map


def _load_sales():
    """Concat all 2024–2026 sales CSVs + post-flight actuals, filter to Perishable + pair flights."""
    frames = []
    for fp in SALES_FILES:
        if fp.exists():
            frames.append(pd.read_csv(fp, low_memory=False))
    for fp in sorted(ACTUALS_DIR.glob("sales_*.csv")):
        try:
            frames.append(pd.read_csv(fp, low_memory=False))
        except Exception:
            pass
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    
    # Identify category columns safely to capture perishables on all days
    npc_col = None
    pc_col = None
    for c in df.columns:
        c_low = c.lower().strip()
        if c_low == "new_product_category":
            npc_col = c
        elif c_low == "product_category":
            pc_col = c
            
    mask = pd.Series(False, index=df.index)
    if npc_col:
        mask = mask | (df[npc_col].astype(str).str.strip().str.lower() == "perishable")
    if pc_col:
        mask = mask | (df[pc_col].astype(str).str.strip().str.lower() == "perishable")
        
    df = df[mask].copy()
    flt_col = _col(df, "flightnum")
    df = df[df[flt_col].isin(PAIR_FLIGHTS)].copy()
    return df


def _load_wastage():
    """Concat all 2024–2026 wastage CSVs."""
    frames = []
    for fp in WASTAGE_FILES:
        if fp.exists():
            frames.append(pd.read_csv(fp))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _load_net_bob_history():
    """Return {date_str: net_bob} for all historical pair-route flight dates.
    Counts all pax across both legs (175+176) since sales are also aggregated across both legs.
    net_bob = total_pax_both_legs - perishable_PBM_bookings (water codes excluded).
    """
    # 1. Scan single-date uploaded files to de-duplicate and capture path mappings
    uploaded_pax_paths = {}
    for p in UPLOAD_DIR.glob("pax_*.csv"):
        uploaded_pax_paths[p.stem.replace("pax_", "")] = p
    for p in ACTUALS_DIR.glob("pax_*.csv"):
        uploaded_pax_paths[p.stem.replace("pax_", "")] = p

    uploaded_pbm_paths = {}
    for p in UPLOAD_DIR.glob("pbm_*.csv"):
        uploaded_pbm_paths[p.stem.replace("pbm_", "")] = p

    # 2. Compute pax per date
    pax_per_date = {}
    
    # 2a. Load historical passenger files
    hist_pax_frames = []
    for fp in PAX_FILES:
        if fp.exists():
            try:
                hist_pax_frames.append(pd.read_csv(fp, usecols=["FlightDate"], low_memory=False))
            except Exception as e:
                print(f"[WARN] Failed to load historical pax file {fp.name}: {e}")
                
    if hist_pax_frames:
        hist_pax_df = pd.concat(hist_pax_frames, ignore_index=True)
        hist_pax_df["FlightDate"] = pd.to_datetime(hist_pax_df["FlightDate"], errors="coerce").dt.strftime("%Y-%m-%d")
        hist_pax_df = hist_pax_df.dropna(subset=["FlightDate"])
        # Exclude dates that are covered by single-date uploads to prevent duplicate counting
        hist_pax_df = hist_pax_df[~hist_pax_df["FlightDate"].isin(uploaded_pax_paths.keys())]
        pax_per_date = hist_pax_df.groupby("FlightDate").size().to_dict()
        
    # 2b. Override/add with single-date uploaded passenger files
    for date_str, fp in uploaded_pax_paths.items():
        try:
            df = pd.read_csv(fp, usecols=["FlightDate"], low_memory=False)
            df["FlightDate"] = pd.to_datetime(df["FlightDate"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df.dropna(subset=["FlightDate"])
            # Record counts grouped by date
            for d, grp in df.groupby("FlightDate"):
                pax_per_date[str(d)] = len(grp)
        except Exception as e:
            print(f"[WARN] Failed to load uploaded pax file {fp.name}: {e}")

    # 3. Compute PBM per date (excluding water codes)
    pbm_per_date = {}
    
    # 3a. Load historical PBM files
    hist_pbm_frames = []
    for fp in PBM_FILES:
        if fp.exists():
            try:
                hist_pbm_frames.append(pd.read_csv(fp, usecols=["FlightDate", "SSRCode"], low_memory=False))
            except Exception as e:
                print(f"[WARN] Failed to load historical PBM file {fp.name}: {e}")
                
    if hist_pbm_frames:
        hist_pbm_df = pd.concat(hist_pbm_frames, ignore_index=True)
        hist_pbm_df["FlightDate"] = pd.to_datetime(hist_pbm_df["FlightDate"], errors="coerce").dt.strftime("%Y-%m-%d")
        hist_pbm_df = hist_pbm_df.dropna(subset=["FlightDate"])
        hist_pbm_df = hist_pbm_df[~hist_pbm_df["SSRCode"].isin(WATER_CODES)]
        # Exclude dates that are covered by single-date uploads to prevent duplicate counting
        hist_pbm_df = hist_pbm_df[~hist_pbm_df["FlightDate"].isin(uploaded_pbm_paths.keys())]
        pbm_per_date = hist_pbm_df.groupby("FlightDate").size().to_dict()
        
    # 3b. Override/add with single-date uploaded PBM files
    for date_str, fp in uploaded_pbm_paths.items():
        try:
            df = pd.read_csv(fp, usecols=["FlightDate", "SSRCode"], low_memory=False)
            df["FlightDate"] = pd.to_datetime(df["FlightDate"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df.dropna(subset=["FlightDate"])
            df = df[~df["SSRCode"].isin(WATER_CODES)]
            for d, grp in df.groupby("FlightDate"):
                pbm_per_date[str(d)] = len(grp)
        except Exception as e:
            print(f"[WARN] Failed to load uploaded PBM file {fp.name}: {e}")

    # 4. Combine and calculate net_bob
    all_dates = set(pax_per_date.keys()) | set(pbm_per_date.keys())
    net_bob_map = {}
    for d in all_dates:
        pax = pax_per_date.get(d, 0)
        pbm = pbm_per_date.get(d, 0)
        net_bob_map[d] = max(0, pax - pbm)
        
    return net_bob_map


def _build_preference_weights():
    """
    Step 1 of A1 demographic override.
    Join PAX (seat + nationality) to SALES (seat + SKU) across all historical dates.
    Returns {country: {sku_code: avg_units_per_pax_of_that_country}}.
    Returns {} and logs warning if seat column absent or join too sparse.
    Result cached for the server lifetime; invalidated when post-flight actuals arrive.
    """
    global _pref_weights_cache
    if _pref_weights_cache is not None:
        return _pref_weights_cache

    # Scan single-date uploaded pax files
    uploaded_pax_paths = {}
    for p in UPLOAD_DIR.glob("pax_*.csv"):
        uploaded_pax_paths[p.stem.replace("pax_", "")] = p
    for p in ACTUALS_DIR.glob("pax_*.csv"):
        uploaded_pax_paths[p.stem.replace("pax_", "")] = p

    pax_frames = []
    for fp in PAX_FILES:
        if fp.exists():
            try:
                df = pd.read_csv(fp, usecols=["FlightDate", "UnitDesignator", "Country_name"],
                                 low_memory=False)
                df = df.rename(columns={"FlightDate": "date", "UnitDesignator": "seat",
                                        "Country_name": "country"})
                df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
                df = df.dropna(subset=["date"])
                # Exclude dates that are covered by single-date uploads to prevent duplicate counting
                df = df[~df["date"].isin(uploaded_pax_paths.keys())]
                pax_frames.append(df)
            except Exception as e:
                print(f"[WARN] _build_preference_weights: failed to load historical {fp.name}: {e}")

    for date_str, fp in uploaded_pax_paths.items():
        try:
            df = pd.read_csv(fp, usecols=["FlightDate", "UnitDesignator", "Country_name"],
                             low_memory=False)
            df = df.rename(columns={"FlightDate": "date", "UnitDesignator": "seat",
                                    "Country_name": "country"})
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df.dropna(subset=["date"])
            pax_frames.append(df)
        except Exception as e:
            print(f"[WARN] _build_preference_weights: failed to load uploaded {fp.name}: {e}")

    if not pax_frames:
        _pref_weights_cache = {}
        return {}

    pax_df = pd.concat(pax_frames, ignore_index=True)
    pax_df["seat"]    = pax_df["seat"].astype(str).str.strip().str.upper()
    pax_df["country"] = pax_df["country"].astype(str).str.strip()
    pax_df = pax_df.dropna(subset=["date", "seat"])

    sales_df = _load_sales()
    if sales_df.empty:
        _pref_weights_cache = {}
        return {}

    code_col = _col(sales_df, "product_code")
    qty_col  = _col(sales_df, "quantity")
    date_col = _col(sales_df, "flight_date")

    low_map = {c.lower().strip(): c for c in sales_df.columns}
    seat_col_sales = next(
        (low_map[k] for k in ["seat_number", "seatnumber", "seat"] if k in low_map), None
    )
    if not seat_col_sales:
        print("[WARN] _build_preference_weights: no seat column found in sales — demographic γ disabled")
        _pref_weights_cache = {}
        return {}

    s = sales_df[[date_col, seat_col_sales, code_col, qty_col]].copy()
    s = s.rename(columns={date_col: "date", seat_col_sales: "seat",
                           code_col: "sku", qty_col: "qty"})
    s["date"] = pd.to_datetime(s["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    s["seat"] = s["seat"].astype(str).str.strip().str.upper()
    s["qty"]  = pd.to_numeric(s["qty"], errors="coerce").fillna(0)
    s = s.dropna(subset=["date", "seat"])

    merged = s.merge(pax_df[["date", "seat", "country"]], on=["date", "seat"], how="inner")

    if len(merged) < 500:
        print(f"[WARN] _build_preference_weights: seat join returned only {len(merged)} rows — demographic γ disabled")
        _pref_weights_cache = {}
        return {}

    print(f"[INFO] _build_preference_weights: seat join produced {len(merged):,} matches across "
          f"{merged['country'].nunique()} nationalities, {merged['sku'].nunique()} SKUs")

    sku_by_nat   = merged.groupby(["country", "sku"])["qty"].sum()
    country_pax  = pax_df.groupby("country").size().astype(float)

    weights = {}
    for (country, sku), units in sku_by_nat.items():
        weights.setdefault(country, {})[sku] = float(units) / country_pax.get(country, 1.0)

    _pref_weights_cache = weights
    return weights


def _get_monthly_nat_fracs(month):
    """
    Step 2 helper — historical nationality composition for a given calendar month.
    Returns {country: fraction} summing to 1.0.
    """
    global _monthly_nat_cache
    if month in _monthly_nat_cache:
        return _monthly_nat_cache[month]

    # Scan single-date uploaded pax files
    uploaded_pax_paths = {}
    for p in UPLOAD_DIR.glob("pax_*.csv"):
        uploaded_pax_paths[p.stem.replace("pax_", "")] = p
    for p in ACTUALS_DIR.glob("pax_*.csv"):
        uploaded_pax_paths[p.stem.replace("pax_", "")] = p

    pax_frames = []
    for fp in PAX_FILES:
        if fp.exists():
            try:
                df = pd.read_csv(fp, usecols=["FlightDate", "Country_name"], low_memory=False)
                df["FlightDate"] = pd.to_datetime(df["FlightDate"], errors="coerce").dt.strftime("%Y-%m-%d")
                df = df.dropna(subset=["FlightDate"])
                df = df[~df["FlightDate"].isin(uploaded_pax_paths.keys())]
                pax_frames.append(df)
            except Exception:
                pass

    for date_str, fp in uploaded_pax_paths.items():
        try:
            df = pd.read_csv(fp, usecols=["FlightDate", "Country_name"], low_memory=False)
            df["FlightDate"] = pd.to_datetime(df["FlightDate"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df.dropna(subset=["FlightDate"])
            pax_frames.append(df)
        except Exception:
            pass

    if not pax_frames:
        _monthly_nat_cache[month] = {}
        return {}

    pax_df = pd.concat(pax_frames, ignore_index=True)
    pax_df["_month"]      = pd.to_datetime(pax_df["FlightDate"], errors="coerce").dt.month
    pax_df["Country_name"] = pax_df["Country_name"].astype(str).str.strip()

    month_df = pax_df[pax_df["_month"] == month]
    if month_df.empty:
        _monthly_nat_cache[month] = {}
        return {}

    counts = month_df["Country_name"].value_counts()
    total  = float(counts.sum())
    fracs  = {k: float(v) / total for k, v in counts.items()}
    _monthly_nat_cache[month] = fracs
    return fracs


def _compute_gamma(nat_counts, month, sku_codes):
    """
    Step 2 of A1 — compute demographic multiplier γ per SKU.

    nat_counts: {country: raw_count} from the uploaded manifest
    month: calendar month int of the upcoming flight
    sku_codes: list of SKU code strings

    γ = upcoming_weighted_demand_rate / historical_month_weighted_demand_rate
    γ > 1 → flight is heavier than normal on buyers of that SKU (load more)
    γ < 1 → flight is lighter (load less)
    γ = 1 if preference data is unavailable for this SKU.
    """
    pref = _build_preference_weights()
    hist = _get_monthly_nat_fracs(month)

    if not pref or not hist:
        return {sku: 1.0 for sku in sku_codes}

    total    = float(sum(nat_counts.values())) or 1.0
    upcoming = {k: v / total for k, v in nat_counts.items()}

    all_countries = set(list(upcoming.keys()) + list(hist.keys()))

    gammas = {}
    for sku in sku_codes:
        sku_pref = {c: pref.get(c, {}).get(sku, 0.0) for c in all_countries}
        if sum(sku_pref.values()) < 1e-9:
            gammas[sku] = 1.0
            continue

        upcoming_rate = sum(upcoming.get(c, 0.0) * sku_pref[c] for c in all_countries)
        hist_rate     = sum(hist.get(c, 0.0)     * sku_pref[c] for c in all_countries)

        gammas[sku] = round(upcoming_rate / hist_rate, 4) if hist_rate >= 1e-9 else 1.0

    return gammas


def _retail_prices(sales_df):
    """Return {code: modal_price} from sales transactions."""
    if sales_df.empty:
        return {}
    code_col  = _col(sales_df, "product_code")
    price_col = _col(sales_df, "product_price")
    prices = {}
    for code, grp in sales_df.groupby(code_col):
        prices[str(code).strip()] = float(grp[price_col].mode().iloc[0])
    return prices


def _product_names(sales_df):
    """Return {code: name}."""
    if sales_df.empty:
        return {}
    code_col = _col(sales_df, "product_code")
    name_col = _col(sales_df, "product")
    names = {}
    for code, grp in sales_df.groupby(code_col):
        names[str(code).strip()] = str(grp[name_col].iloc[0])
    return names

# ══════════════════════════════════════════════════════════════════════════
#  MENU STATE
# ══════════════════════════════════════════════════════════════════════════

def _load_menu():
    if MENU_FILE.exists():
        with open(MENU_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_menu(data):
    with open(MENU_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _build_initial_menu():
    """Build menu from sales + cost data."""
    sales_df    = _load_sales()
    cost_map    = _load_cost_map()
    prices      = _retail_prices(sales_df)
    names       = _product_names(sales_df)
    all_codes   = sorted(set(list(prices.keys()) + list(cost_map.keys())))
    items = []
    for code in all_codes:
        if code not in names:
            continue  # only items that appear in perishable sales
        items.append({
            "code":   code,
            "name":   names.get(code, code),
            "active": True,
            "price":  prices.get(code, 0),
            "cost":   cost_map.get(code, 0),
        })
    menu = {"items": items}
    _save_menu(menu)
    return menu


# ══════════════════════════════════════════════════════════════════════════
#  THEORY PIPELINE
# ══════════════════════════════════════════════════════════════════════════

def _tobit_neg_ll(params, obs, caps, weights=None):
    """Negative log-likelihood for censored normal (Tobit).
    obs: observed daily demand array
    caps: loaded quantity array (same length); np.inf if unknown
    weights: weight factor for each observation
    """
    mu, log_sigma = params
    sigma = np.exp(log_sigma)
    if sigma < 1e-6:
        return 1e12
    uncensored = obs < caps
    ll_terms = np.where(
        uncensored,
        norm.logpdf(obs, mu, sigma),
        np.log(np.maximum(1.0 - norm.cdf(caps, mu, sigma), 1e-15))
    )
    if weights is not None:
        ll_terms = ll_terms * weights
    return -ll_terms.sum()


def _compute_yoy_ratios(sales_df, net_bob_map):
    """
    Computes a Year-over-Year scaling ratio per SKU (2026 average rate / pre-2026 average rate).
    Returns ({sku: ratio}, system_avg_ratio).
    If a SKU has no pre-2026 baseline or no 2026 data, it won't have a SKU-specific ratio.
    The system_avg_ratio is the average of all valid SKU ratios, capped between 0.4 and 1.5.
    """
    if sales_df.empty or not net_bob_map:
        return {}, 1.0

    code_col = _col(sales_df, "product_code")
    qty_col  = _col(sales_df, "quantity")
    date_col = _col(sales_df, "flight_date")

    df = sales_df[[code_col, qty_col, date_col]].copy()
    df["date_str"] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
    df["year"] = pd.to_datetime(df[date_col], errors="coerce").dt.year
    df = df.dropna(subset=["date_str", "year"])
    
    # Sum both legs per product & date
    daily = df.groupby(["date_str", "year", code_col])[qty_col].sum().reset_index()
    daily["net_bob"] = daily["date_str"].map(net_bob_map).fillna(0).astype(int)
    daily = daily[daily["net_bob"] > 0].copy()
    daily["rate"] = daily[qty_col] / daily["net_bob"]

    sku_ratios = {}
    sku_list = daily[code_col].astype(str).str.strip().unique()

    for sku in sku_list:
        sku_df = daily[daily[code_col].astype(str).str.strip() == sku]
        rate_2026 = sku_df[sku_df["year"] == 2026]["rate"]
        rate_prev = sku_df[sku_df["year"] < 2026]["rate"]

        if not rate_2026.empty and not rate_prev.empty:
            avg_2026 = float(rate_2026.mean())
            avg_prev = float(rate_prev.mean())
            if avg_prev > 1e-9:
                # Cap SKU ratio between 0.4 and 1.5 to keep logic highly robust
                sku_ratios[sku] = min(max(avg_2026 / avg_prev, 0.4), 1.5)

    if sku_ratios:
        system_avg = float(np.mean(list(sku_ratios.values())))
        system_avg = min(max(system_avg, 0.4), 1.5)
    else:
        system_avg = 1.0

    return sku_ratios, system_avg


def run_pipeline(active_items, demographics=None):
    """Execute the 7-theory pipeline for each active perishable item.

    demographics is required for a flight-specific forecast (enforced by /api/forecast).
    When None (actuals endpoint), uses average historical net_bob as a display proxy.
    """
    sales_df    = _load_sales()
    wastage_df  = _load_wastage()
    cost_map    = _load_cost_map()
    prices      = _retail_prices(sales_df)
    net_bob_map = _load_net_bob_history()
    actuals_dates = {fp.stem.replace("sales_", "") for fp in ACTUALS_DIR.glob("sales_*.csv")}
    sku_yoy_ratios, system_yoy_ratio = _compute_yoy_ratios(sales_df, net_bob_map)


    if sales_df.empty:
        return []

    code_col = _col(sales_df, "product_code")
    qty_col  = _col(sales_df, "quantity")
    date_col = _col(sales_df, "flight_date")

    w_code_col = w_date_col = w_open_col = None
    if not wastage_df.empty:
        w_code_col = _col(wastage_df, "prtnum")
        w_date_col = _col(wastage_df, "flightdate")
        w_open_col = _col(wastage_df, "open_quantity")

    # Determine upcoming flight context
    if demographics:
        total_pax_up   = demographics.get("total_pax", 0)
        pbm_count_up   = demographics.get("pbm_count", 0)
        net_bob_up     = max(0, total_pax_up - pbm_count_up)
        fdate          = demographics.get("flight_date")
        upcoming_month = pd.to_datetime(fdate).month if fdate else pd.Timestamp.today().month
    else:
        net_bob_up     = int(np.mean(list(net_bob_map.values()))) if net_bob_map else 194
        upcoming_month = pd.Timestamp.today().month

    # Pre-compute demographic gamma (A1) — runs once for all SKUs
    nat_counts = demographics.get("nationalities", {}) if demographics else {}
    sku_list   = [it["code"] for it in active_items]
    gammas     = _compute_gamma(nat_counts, upcoming_month, sku_list) if nat_counts else {}

    # Load full menu state to get inactive proxy item metadata during Pass 1
    menu = _load_menu()
    if menu is None:
        menu = _build_initial_menu()
    all_items_map = {it["code"]: it for it in menu["items"]}

    active_codes = {it["code"] for it in active_items}
    proxy_codes = {it["proxy_code"] for it in active_items if it.get("proxy_code")}
    codes_to_fit = active_codes | proxy_codes

    computed = {}
    results  = []

    # ── First pass: items WITH sales history (including inactive proxy SKUs) ─────────────────────────────
    for code in sorted(codes_to_fit):
        item = all_items_map.get(code)
        if not item:
            item = {"code": code, "name": code, "active": code in active_codes}

        sku   = item.get("sku", code)   # real CSV lookup code; falls back to code
        proxy = item.get("proxy_code")
        theories = []

        item_sales = sales_df[sales_df[code_col].astype(str).str.strip() == sku].copy()
        if item_sales.empty:
            continue  # no history → defer to proxy pass

        # T1: Pair-Route Aggregation (sum both legs per date)
        daily = (item_sales.groupby(date_col)[qty_col]
                 .sum().reset_index()
                 .rename(columns={date_col: "date", qty_col: "demand"}))
        theories.append("T1:Pair-Route")

        # Add censoring cap from wastage
        daily["cap"] = np.inf
        if not wastage_df.empty and w_code_col:
            w_item = wastage_df[wastage_df[w_code_col].astype(str).str.strip() == sku]
            if not w_item.empty:
                loaded_map = w_item.groupby(w_date_col)[w_open_col].sum().to_dict()
                daily["cap"] = daily["date"].map(loaded_map).fillna(np.inf)

        # Standardize dates and join historical net_bob; drop dates with no pax data
        daily["date_str"] = pd.to_datetime(daily["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        daily = daily.dropna(subset=["date_str"])
        daily["net_bob"] = daily["date_str"].map(net_bob_map).fillna(0).astype(int)
        daily = daily[daily["net_bob"] > 0].copy()
        if daily.empty:
            continue

        # Compute per-pax demand rate for each historical flight
        daily["rate"]     = daily["demand"] / daily["net_bob"]
        daily["cap_rate"] = daily.apply(
            lambda r: r["cap"] / r["net_bob"] if r["cap"] < np.inf else np.inf, axis=1
        )

        # Apply Year-over-Year (YoY) Demand Scaling calibration to pre-2026 historical rates
        if sku in sku_yoy_ratios:
            ratio = sku_yoy_ratios[sku]
            mask_prev = pd.to_datetime(daily["date_str"]).dt.year < 2026
            daily.loc[mask_prev, "rate"] = daily.loc[mask_prev, "rate"] * ratio
            daily.loc[mask_prev, "cap_rate"] = daily.loc[mask_prev, "cap_rate"] * ratio
            theories.append(f"T1b:YoYScale(SKU_ratio={ratio:.3f},applied_to_pre2026)")
        else:
            ratio = system_yoy_ratio
            mask_prev = pd.to_datetime(daily["date_str"]).dt.year < 2026
            daily.loc[mask_prev, "rate"] = daily.loc[mask_prev, "rate"] * ratio
            daily.loc[mask_prev, "cap_rate"] = daily.loc[mask_prev, "cap_rate"] * ratio
            theories.append(f"T1b:YoYScale(System_ratio={ratio:.3f},applied_to_pre2026_fallback)")

        daily["censored"] = daily["rate"] >= daily["cap_rate"]
        daily["month"]    = pd.to_datetime(daily["date_str"]).dt.month
        n_censored_total  = int(daily["censored"].sum())

        daily["weight"]   = daily["date_str"].apply(lambda d: RECENCY_WEIGHT_FACTOR if d in actuals_dates else 1.0)

        # T2: Per-month Tobit MLE on demand rates
        # Discontinued months are absent from data — handled naturally (no special logic).
        monthly_params = {}
        for month_val, grp in daily.groupby("month"):
            obs_r = grp["rate"].values.astype(float)
            cap_r = grp["cap_rate"].values
            w_r   = grp["weight"].values.astype(float)
            if len(obs_r) < 3:
                continue
            init_mu    = float(np.mean(obs_r))
            init_sigma = float(np.std(obs_r)) if np.std(obs_r) > 0 else 0.01
            try:
                res = minimize(
                    _tobit_neg_ll,
                    x0=[init_mu, np.log(max(init_sigma, 1e-6))],
                    args=(obs_r, cap_r, w_r),
                    method="Nelder-Mead",
                    options={"maxiter": 5000, "xatol": 1e-8, "fatol": 1e-8},
                )
                monthly_params[month_val] = (float(res.x[0]), float(np.exp(res.x[1])))
            except Exception:
                monthly_params[month_val] = (init_mu, max(init_sigma, 1e-4))

        # Global fallback rate (all months pooled — used when upcoming month has no history)
        all_rates = daily["rate"].values.astype(float)
        all_caps  = daily["cap_rate"].values
        all_weights = daily["weight"].values.astype(float)
        init_mu_g    = float(np.mean(all_rates))
        init_sigma_g = float(np.std(all_rates)) if np.std(all_rates) > 0 else 0.01
        try:
            res_g = minimize(
                _tobit_neg_ll,
                x0=[init_mu_g, np.log(max(init_sigma_g, 1e-6))],
                args=(all_rates, all_caps, all_weights),
                method="Nelder-Mead",
                options={"maxiter": 5000, "xatol": 1e-8, "fatol": 1e-8},
            ) if len(all_rates) >= 3 else None
            global_rate = (float(res_g.x[0]), float(np.exp(res_g.x[1]))) if res_g else (init_mu_g, max(init_sigma_g, 1e-4))
        except Exception:
            global_rate = (init_mu_g, max(init_sigma_g, 1e-4))

        mu_rate, sigma_rate = monthly_params.get(upcoming_month, global_rate)
        sigma_rate = max(sigma_rate, 1e-4)
        theories.append(f"T2:Tobit-Rate(months={len(monthly_params)},cens={n_censored_total}/{len(daily)})")

        price = item.get("price") or prices.get(code, 0)
        cost  = item.get("cost")  or cost_map.get(code, 0)

        # T3: Newsvendor cost parameters
        C_o = cost
        C_u = max(price - cost, 0)
        theories.append("T3:Newsvendor")

        # T4: Critical Fractile
        denom  = C_u + C_o
        F_star = C_u / denom if denom > 0 else 0.5
        z      = float(norm.ppf(F_star)) if 0 < F_star < 1 else 0.0
        theories.append(f"T4:CritFrac(F*={F_star:.4f})")

        # T5: Flight-specific Q* via rate × net_bob_upcoming
        mu_flight    = mu_rate * net_bob_up
        sigma_flight = sigma_rate * net_bob_up
        q_newsvendor = max(mu_flight + z * sigma_flight, 0)
        q_baseline_val = math.ceil(q_newsvendor)
        theories.append(f"T5:RateScaled(net_bob={net_bob_up},month={upcoming_month})")

        # T5b: Demographic gamma (A1) — scale by nationality composition deviation
        gamma = gammas.get(code, 1.0)
        if abs(gamma - 1.0) > 0.01:
            theories.append(f"T5b:DemoGamma(γ={gamma:.3f})")
        q_final = math.ceil(max(q_newsvendor * gamma, 0))

        # Expected Profitability Override (Theory 3/4 addon)
        expected_profit = _expected_profit(q_final, mu_flight, sigma_flight, price, cost)
        expected_profit_baseline = expected_profit
        expected_profit_override_applied = False
        
        if q_final > 0:
            if expected_profit <= 0:
                q_final = 0
                expected_profit = 0.0
                expected_profit_override_applied = True
                theories.append(f"ExpectedProfitOverride(profit_at_{q_baseline_val}={expected_profit_baseline:.2f}THB,set_q=0)")

        theories.append("T6:Substitution(skipped,established)")
        if any(ACTUALS_DIR.glob("sales_*.csv")):
            theories.append("T7:MLE-Refit(actuals_incorporated)")

        computed[code] = {"mu_rate": mu_rate, "sigma_rate": sigma_rate}

        # Only append active items to the recommendations list
        if code in active_codes:
            results.append({
                "code":             code,
                "name":             item.get("name", code),
                "price":            round(price, 2),
                "cost":             round(cost, 2),
                "critical_ratio":   round(F_star, 4),
                "stockout_pct":     round((1 - F_star) * 100, 2),
                "mu":               round(mu_flight, 2),
                "sigma":            round(sigma_flight, 2),
                "q_baseline":       q_baseline_val,
                "q_adjusted":       q_final,
                "delta":            q_final - q_baseline_val,
                "gamma":            round(gamma, 3),
                "theories_applied": theories,
                "expected_profit":  round(expected_profit, 2),
                "expected_profit_baseline": round(expected_profit_baseline, 2),
                "expected_profit_override_applied": expected_profit_override_applied,
                "is_new_item":      False
            })

    # ── Second pass: new items via proxy (Theory 6) ───────────────────────
    for item in active_items:
        code  = item["code"]
        proxy = item.get("proxy_code")
        if not proxy or code in computed or proxy not in computed:
            continue

        theories = ["T1:Pair-Route(via_proxy)", "T2:Tobit-Rate(via_proxy)"]

        mu_rate    = computed[proxy]["mu_rate"]
        sigma_rate = computed[proxy]["sigma_rate"]

        price = item.get("price", 0)
        cost  = item.get("cost", 0)
        C_o   = cost
        C_u   = max(price - cost, 0)
        theories.append("T3:Newsvendor")

        denom  = C_u + C_o
        F_star = C_u / denom if denom > 0 else 0.5
        z      = float(norm.ppf(F_star)) if 0 < F_star < 1 else 0.0
        theories.append(f"T4:CritFrac(F*={F_star:.4f})")

        mu_flight    = mu_rate * net_bob_up
        sigma_flight = sigma_rate * net_bob_up
        q_newsvendor = max(mu_flight + z * sigma_flight, 0)
        q_baseline_val = math.ceil(q_newsvendor)
        theories.append(f"T5:RateScaled(net_bob={net_bob_up},month={upcoming_month})")

        gamma = gammas.get(code, 1.0)
        if abs(gamma - 1.0) > 0.01:
            theories.append(f"T5b:DemoGamma(γ={gamma:.3f})")
        q_final = math.ceil(max(q_newsvendor * gamma, 0))

        # Brand new proxy items (Theory 6) are bypassed from Expected Profitability Override 
        # and instead load a minimum of 1 unit during their grace period (to collect empirical demand)
        is_grace_period_applied = False
        if q_final == 0:
            q_final = 1
            is_grace_period_applied = True
            theories.append("ProxyGracePeriod(forced_min_q=1)")
        else:
            theories.append("ProxyGracePeriod(skipped,q>=1)")

        expected_profit = _expected_profit(q_final, mu_flight, sigma_flight, price, cost)

        theories.append(f"T6:Substitution(proxy={proxy})")
        if any(ACTUALS_DIR.glob("sales_*.csv")):
            theories.append("T7:MLE-Refit(actuals_incorporated)")

        results.append({
            "code":             code,
            "name":             item.get("name", code),
            "price":            round(price, 2),
            "cost":             round(cost, 2),
            "critical_ratio":   round(F_star, 4),
            "stockout_pct":     round((1 - F_star) * 100, 2),
            "mu":               round(mu_flight, 2),
            "sigma":            round(sigma_flight, 2),
            "q_baseline":       q_baseline_val,
            "q_adjusted":       q_final,
            "delta":            q_final - q_baseline_val,
            "gamma":            round(gamma, 3),
            "theories_applied": theories,
            "expected_profit":  round(expected_profit, 2),
            "expected_profit_baseline": round(expected_profit, 2),
            "expected_profit_override_applied": False,
            "is_new_item":      True,
            "is_grace_period_applied": is_grace_period_applied
        })

    return results


# ══════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_file(str(HTML_FILE))


@app.route("/api/menu", methods=["GET"])
def get_menu():
    menu = _load_menu()
    if menu is None:
        menu = _build_initial_menu()
    return jsonify(menu)


@app.route("/api/menu/toggle", methods=["POST"])
def toggle_item():
    body = request.get_json(force=True)
    code = body.get("code", "")
    menu = _load_menu()
    if menu is None:
        menu = _build_initial_menu()
    found = False
    for it in menu["items"]:
        if it["code"] == code:
            it["active"] = not it["active"]
            found = True
            break
    if not found:
        return jsonify({"error": f"Item {code} not found"}), 404
    _save_menu(menu)
    return jsonify(menu)


@app.route("/api/menu/add", methods=["POST"])
def add_item():
    body = request.get_json(force=True)
    menu = _load_menu()
    if menu is None:
        menu = _build_initial_menu()
    new_item = {
        "code":       body.get("code", ""),
        "name":       body.get("name", ""),
        "active":     True,
        "price":      float(body.get("price", 0)),
        "cost":       float(body.get("cost", 0)),
        "proxy_code": body.get("proxy_code", None),
    }
    # avoid duplicates
    existing_codes = {it["code"] for it in menu["items"]}
    if new_item["code"] in existing_codes:
        return jsonify({"error": "Item code already exists"}), 409
    menu["items"].append(new_item)
    _save_menu(menu)
    return jsonify(menu), 201


@app.route("/api/upload", methods=["POST"])
def upload_csv():
    """Accept passenger manifest and PBM CSV uploads.
    Extracts FlightDate from first column (Index-0 fallback per Problem C).
    Returns: flight_date, already_uploaded, total_pax, pbm_count, net_bob,
             nationalities, ages.
    """
    pax_file = request.files.get("passenger")
    pbm_file = request.files.get("pbm")

    total_pax            = 0
    pbm_count            = 0
    nationalities        = {}
    ages                 = {}
    flight_date          = None
    pbm_date             = None
    already_uploaded     = False
    pbm_already_uploaded = False
    pax_df               = None
    pbm_df               = None

    # ── Parse both files into memory BEFORE writing anything to disk ──
    if pax_file:
        try:
            pax_df = pd.read_csv(pax_file, low_memory=False)
            # Verify file type: Passenger file must not contain "SSRCode"
            if any(c.lower().strip() == "ssrcode" for c in pax_df.columns):
                return jsonify({"error": "Invalid Passenger Manifest file. It must not contain the 'SSRCode' column. Did you accidentally upload the PBM file as the Passenger Manifest?"}), 400
            flight_date = _extract_flight_date(pax_df)
        except Exception as e:
            if "Invalid Passenger Manifest" in str(e):
                return jsonify({"error": str(e)}), 400
            return jsonify({"error": f"Failed to parse passenger CSV: {e}"}), 400

    if pbm_file:
        try:
            pbm_df = pd.read_csv(pbm_file, low_memory=False)
            # Verify file type: PBM file must contain "SSRCode"
            if not any(c.lower().strip() == "ssrcode" for c in pbm_df.columns):
                return jsonify({"error": "Invalid PBM Booking file. It must contain the 'SSRCode' column. Did you accidentally upload the Passenger Manifest as the PBM file?"}), 400
            pbm_date = _extract_flight_date(pbm_df)
        except Exception as e:
            if "Invalid PBM Booking" in str(e):
                return jsonify({"error": str(e)}), 400
            return jsonify({"error": f"Failed to parse PBM CSV: {e}"}), 400

    # ── Validate dates match before touching disk ─────────────────────
    if flight_date and pbm_date and flight_date != pbm_date:
        return jsonify({
            "error": f"Date mismatch: passenger manifest is {flight_date} but PBM file is {pbm_date}. Upload matching files."
        }), 400

    # ── Save pax and extract demographics ─────────────────────────────
    if pax_df is not None:
        if flight_date:
            marker = UPLOAD_DIR / f"pax_{flight_date}.csv"
            already_uploaded = marker.exists()
            pax_df.to_csv(str(marker), index=False)
        else:
            pax_df.to_csv(str(UPLOAD_DIR / pax_file.filename), index=False)

        total_pax = len(pax_df)

        nat_col = _col(pax_df, "country_name")
        all_counts = pax_df[nat_col].astype(str).str.strip().value_counts()
        if not all_counts.empty:
            top5 = all_counts.head(5)
            for nat, cnt in top5.items():
                nationalities[nat] = int(cnt)
            rest = int(all_counts.iloc[5:].sum()) if len(all_counts) > 5 else 0
            if rest > 0:
                nationalities["Others"] = rest

        age_col = _col(pax_df, "paxage")
        a = pd.to_numeric(pax_df[age_col], errors="coerce")
        if a.notna().any():
            ages["0-17"]  = int((a < 18).sum())
            ages["18-35"] = int(((a >= 18) & (a <= 35)).sum())
            ages["36-55"] = int(((a >= 36) & (a <= 55)).sum())
            ages["56+"]   = int((a > 55).sum())

    # ── Save PBM and count food-only rows (exclude water codes) ───────
    if pbm_df is not None:
        if pbm_date:
            marker = UPLOAD_DIR / f"pbm_{pbm_date}.csv"
            pbm_already_uploaded = marker.exists()
            pbm_df.to_csv(str(marker), index=False)
        else:
            pbm_df.to_csv(str(UPLOAD_DIR / pbm_file.filename), index=False)

        ssr_col = _col(pbm_df, "SSRCode")
        if ssr_col in pbm_df.columns:
            pbm_count = int((~pbm_df[ssr_col].isin(WATER_CODES)).sum())
        else:
            pbm_count = len(pbm_df)

    return jsonify({
        "flight_date":          flight_date,
        "already_uploaded":     already_uploaded,
        "pbm_already_uploaded": pbm_already_uploaded,
        "total_pax":            total_pax,
        "pbm_count":            pbm_count,
        "net_bob":              total_pax - pbm_count,
        "nationalities":        nationalities,
        "ages":                 ages,
    })


@app.route("/api/forecast", methods=["POST"])
def forecast():
    body = request.get_json(force=True) if request.is_json else {}
    demographics = body.get("demographics", None)

    if not demographics or demographics.get("total_pax", 0) == 0:
        return jsonify({
            "error": "Passenger manifest required. Upload the flight manifest and PBM file before running the forecast."
        }), 400

    menu = _load_menu()
    if menu is None:
        menu = _build_initial_menu()

    active_items = [it for it in menu["items"] if it.get("active", True)]

    if not active_items:
        return jsonify({"error": "No active menu items"}), 400

    print(f"\n{'='*60}")
    print(f"  Running 7-Theory Pipeline for {len(active_items)} active items")
    print(f"  Demographics: {'provided' if demographics else 'none'}")
    print(f"{'='*60}")

    results = run_pipeline(active_items, demographics)

    for r in results:
        print(f"  {r['code']} | {r['name'][:40]:<40s} | Q*={r['q_adjusted']:>3d} | "
              f"mu={r['mu']:.1f} sigma={r['sigma']:.1f} | "
              f"Theories: {', '.join(r['theories_applied'])}")

    print(f"{'='*60}\n")

    return jsonify(results)


@app.route("/api/train", methods=["POST"])
def train():
    sales_file = request.files.get("sales_file")
    pax_file = request.files.get("passenger_file")
    
    if not sales_file or not pax_file:
        return jsonify({"error": "Missing sales_file or passenger_file"}), 400
        
    try:
        df_sales = pd.read_csv(sales_file, low_memory=False)
        df_pax = pd.read_csv(pax_file, low_memory=False)
        
        sales_seat = _col(df_sales, "seat")
        pax_seat = _col(df_pax, "seat")
        
        # Nationality column resolution
        nat_col = None
        for c in df_pax.columns:
            c_low = c.lower().strip()
            if c_low in ["nationality", "nat", "country_name"]:
                nat_col = c
                break
        if not nat_col:
            nat_col = _col(df_pax, "nationality")  # fallback to index 0
            
        item_col = _col(df_sales, "product")
        qty_col = _col(df_sales, "quantity")
        
        merged = df_sales.merge(df_pax, left_on=sales_seat, right_on=pax_seat, how="inner")
        
        insights = {}
        for nat, grp in merged.groupby(nat_col):
            nat_str = str(nat).strip()
            item_summary = {}
            for item, item_grp in grp.groupby(item_col):
                item_str = str(item).strip()
                item_summary[item_str] = int(pd.to_numeric(item_grp[qty_col], errors="coerce").fillna(1).sum())
            insights[nat_str] = item_summary
            
        return jsonify({
            "message": "Training complete",
            "demographic_insights": insights,
            "total_matches": len(merged)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/actuals", methods=["POST"])
def post_flight_actuals():
    """Accept actual post-flight sales + wastage + boarded passenger CSVs.
    Appends to ACTUALS_DIR (permanent record), then re-runs Tobit MLE
    on the full updated dataset — this IS Theory 7 (MLE refit on combined dataset).
    """
    sales_file   = request.files.get("sales")
    wastage_file = request.files.get("wastage")
    pax_file     = request.files.get("passenger")

    # Boarded passenger manifest is strictly required
    if not pax_file:
        return jsonify({"error": "Actual Boarded Passenger Manifest is required. Please upload the final manifest CSV exported from PSS."}), 400

    # At least one of sales or wastage is required
    if not sales_file and not wastage_file:
        return jsonify({"error": "Provide at least one file: actual sales or wastage CSV."}), 400

    saved        = []
    flight_date  = None
    pax_df       = None
    sales_df     = None
    wastage_df   = None

    # ── Parse passenger file into memory BEFORE writing anything to disk ──
    try:
        pax_df = pd.read_csv(pax_file, low_memory=False)
        # Verify file type: Passenger file must not contain "SSRCode"
        if any(c.lower().strip() == "ssrcode" for c in pax_df.columns):
            return jsonify({"error": "Invalid Passenger Manifest file. It must not contain the 'SSRCode' column. Did you accidentally upload the PBM file as the Passenger Manifest?"}), 400
        flight_date = _extract_flight_date(pax_df)
        if not flight_date:
            return jsonify({"error": "Could not extract flight date from Passenger Manifest."}), 400
    except Exception as e:
        if "Invalid Passenger Manifest" in str(e):
            return jsonify({"error": str(e)}), 400
        return jsonify({"error": f"Failed to parse passenger CSV: {e}"}), 400

    # ── Parse sales file if provided ──
    if sales_file:
        try:
            sales_df = pd.read_csv(sales_file, low_memory=False)
            # Verify file type: Sales file must contain "transaction_id"
            if not any(c.lower().strip() == "transaction_id" for c in sales_df.columns):
                return jsonify({"error": "Invalid Sales file. It must contain the 'transaction_id' column. Did you accidentally upload the wrong file as Sales?"}), 400
            sales_date = _extract_flight_date(sales_df)
            if not sales_date or sales_date != flight_date:
                return jsonify({"error": f"Date mismatch: passenger manifest date is {flight_date} but sales file date is {sales_date or 'unknown'}."}), 400
        except Exception as e:
            if "Invalid Sales" in str(e):
                return jsonify({"error": str(e)}), 400
            return jsonify({"error": f"Failed to parse sales CSV: {e}"}), 400

    # ── Parse wastage file if provided ──
    if wastage_file:
        try:
            wastage_df = pd.read_csv(wastage_file, low_memory=False)
            # Verify file type: Wastage file must contain "wastage"
            if not any(c.lower().strip() == "wastage" for c in wastage_df.columns):
                return jsonify({"error": "Invalid Wastage file. It must contain the 'wastage' column. Did you accidentally upload the wrong file as Wastage?"}), 400
            wastage_date = _extract_flight_date(wastage_df)
            if not wastage_date or wastage_date != flight_date:
                return jsonify({"error": f"Date mismatch: passenger manifest date is {flight_date} but wastage file date is {wastage_date or 'unknown'}."}), 400
        except Exception as e:
            if "Invalid Wastage" in str(e):
                return jsonify({"error": str(e)}), 400
            return jsonify({"error": f"Failed to parse wastage CSV: {e}"}), 400

    # ── All validations passed, write files to disk ───────────────────
    try:
        pax_fname = f"pax_{flight_date}.csv"
        pax_df.to_csv(str(ACTUALS_DIR / pax_fname), index=False)
        saved.append(pax_fname)

        if sales_df is not None:
            sales_fname = f"sales_{flight_date}.csv"
            sales_df.to_csv(str(ACTUALS_DIR / sales_fname), index=False)
            saved.append(sales_fname)

        if wastage_df is not None:
            wastage_fname = f"wastage_{flight_date}.csv"
            wastage_df.to_csv(str(ACTUALS_DIR / wastage_fname), index=False)
            saved.append(wastage_fname)
    except Exception as e:
        return jsonify({"error": f"Failed to save uploaded files: {e}"}), 500

    # Invalidate preference weights and monthly nationality caches so next forecast picks up the new actuals
    global _pref_weights_cache, _monthly_nat_cache
    _pref_weights_cache = None
    _monthly_nat_cache = {}

    # Re-run pipeline on historical + new actuals → Theory 7 update
    menu = _load_menu()
    bayesian_updates = []
    if menu:
        active_items = [it for it in menu["items"] if it.get("active", True)]
        updated = run_pipeline(active_items)
        bayesian_updates = [
            {"code": r["code"], "name": r["name"],
             "mu": r["mu"], "sigma": r["sigma"], "q_star": r["q_adjusted"]}
            for r in updated
        ]

    return jsonify({
        "message":          f"Actuals saved. Model updated with data from {flight_date}.",
        "flight_date":      flight_date,
        "files_saved":      saved,
        "products_updated": len(bayesian_updates),
        "bayesian_updates": bayesian_updates,
    })


@app.route("/api/daily-sales", methods=["GET"])
def daily_sales():
    """Return daily sales + wastage data from post-flight actuals uploads only."""
    # Load menu items to identify perishables for wastage rows that might have 0 sales
    menu = _load_menu()
    perishable_codes = set()
    if menu:
        perishable_codes = {item["code"] for item in menu["items"]}
        
    # Find all available upload dates in ACTUALS_DIR
    dates = []
    for fp in ACTUALS_DIR.glob("sales_*.csv"):
        stem = fp.stem
        if stem.startswith("sales_"):
            date_str = stem[len("sales_"):]
            dates.append(date_str)
    dates = sorted(list(set(dates)))
    
    if not dates:
        return jsonify({"daily": [], "message": "No post-flight actuals uploaded yet"})
        
    daily = []
    for date_val in dates:
        sales_path = ACTUALS_DIR / f"sales_{date_val}.csv"
        wastage_path = ACTUALS_DIR / f"wastage_{date_val}.csv"
        
        # 1. Process sales data
        sales_dict = {}
        if sales_path.exists():
            try:
                df_sales = pd.read_csv(sales_path, low_memory=False)
                
                # Identify category columns safely
                npc_col = None
                pc_col = None
                for c in df_sales.columns:
                    c_low = c.lower().strip()
                    if c_low == "new_product_category":
                        npc_col = c
                    elif c_low == "product_category":
                        pc_col = c
                        
                mask = pd.Series(False, index=df_sales.index)
                if npc_col:
                    mask = mask | (df_sales[npc_col].astype(str).str.strip().str.lower() == "perishable")
                if pc_col:
                    mask = mask | (df_sales[pc_col].astype(str).str.strip().str.lower() == "perishable")
                    
                df_sales = df_sales[mask].copy()
                
                flt_col = _col(df_sales, "flightnum")
                df_sales = df_sales[df_sales[flt_col].isin(PAIR_FLIGHTS)].copy()
                
                code_col  = _col(df_sales, "product_code")
                name_col  = _col(df_sales, "product")
                qty_col   = _col(df_sales, "quantity")
                price_col = _col(df_sales, "product_price")
                
                df_sales["_qty"] = pd.to_numeric(df_sales[qty_col],   errors="coerce").fillna(0)
                df_sales["_rev"] = pd.to_numeric(df_sales[price_col], errors="coerce").fillna(0) * df_sales["_qty"]
                
                sales_agg = df_sales.groupby(code_col).agg(
                    units=("_qty", "sum"),
                    revenue=("_rev", "sum"),
                    name=(name_col, "first")
                ).reset_index()
                
                for _, row in sales_agg.iterrows():
                    code = str(row[code_col]).strip()
                    sales_dict[code] = {
                        "units": int(row["units"]),
                        "revenue": round(float(row["revenue"]), 2),
                        "name": str(row["name"])
                    }
            except Exception as e:
                print(f"[WARN] Error reading sales CSV for date {date_val}: {e}")
                
        # 2. Process wastage data
        wast_dict = {}
        if wastage_path.exists():
            try:
                df_wast = pd.read_csv(wastage_path, low_memory=False)
                w_flt_col = _col(df_wast, "flightno")
                w_code_col = _col(df_wast, "prtnum")
                w_name_col = _col(df_wast, "product_name")
                w_open_col = _col(df_wast, "open_quantity")
                w_waste_col = _col(df_wast, "wastage")
                
                df_wast = df_wast[df_wast[w_flt_col].isin(PAIR_FLIGHTS)].copy()
                
                df_wast["_open"] = pd.to_numeric(df_wast[w_open_col], errors="coerce").fillna(0)
                df_wast["_waste"] = pd.to_numeric(df_wast[w_waste_col], errors="coerce").fillna(0)
                
                wast_agg = df_wast.groupby(w_code_col).agg(
                    open_qty=("_open", "sum"),
                    waste_qty=("_waste", "sum"),
                    name=(w_name_col, "first")
                ).reset_index()
                
                for _, row in wast_agg.iterrows():
                    code = str(row[w_code_col]).strip()
                    wast_dict[code] = {
                        "open_qty": int(row["open_qty"]),
                        "waste_qty": int(row["waste_qty"]),
                        "name": str(row["name"])
                    }
            except Exception as e:
                print(f"[WARN] Error reading wastage CSV for date {date_val}: {e}")
                
        # 3. Merge products
        all_product_codes = set(sales_dict.keys()) | set(wast_dict.keys())
        
        # Keep only perishable items (either in perishable sales, or in the active menu)
        filtered_codes = [code for code in all_product_codes if (code in sales_dict or code in perishable_codes)]
        
        products = []
        total_units = 0
        total_revenue = 0.0
        total_open = 0
        total_waste = 0
        
        for code in filtered_codes:
            s_row = sales_dict.get(code)
            w_row = wast_dict.get(code)
            
            name = s_row["name"] if s_row else (w_row["name"] if w_row else code)
            units = s_row["units"] if s_row else 0
            revenue = s_row["revenue"] if s_row else 0.0
            
            open_qty = w_row["open_qty"] if w_row else 0
            waste_qty = w_row["waste_qty"] if w_row else 0
            
            products.append({
                "code": code,
                "name": name,
                "units": units,
                "revenue": revenue,
                "open_qty": open_qty,
                "waste_qty": waste_qty
            })
            
            total_units += units
            total_revenue += revenue
            total_open += open_qty
            total_waste += waste_qty
            
        products.sort(key=lambda x: x["units"], reverse=True)
        
        daily.append({
            "date": str(date_val),
            "total_units": total_units,
            "total_revenue": round(total_revenue, 2),
            "total_open": total_open,
            "total_waste": total_waste,
            "products": products
        })
        
    daily.sort(key=lambda x: x["date"])
    return jsonify({"daily": daily})


# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("IFS-AI Perishable Demand Forecasting Server")
    print(f"  Data dir:  {DATA_DIR}")
    print(f"  Dashboard: {HTML_FILE}")
    print(f"  Menu file: {MENU_FILE}")
    print(f"  Starting on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
