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

import json, math, os, warnings
from pathlib import Path

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
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ACTUALS_DIR = UPLOAD_DIR / "actuals"
ACTUALS_DIR.mkdir(exist_ok=True)

COST_FILE     = DATA_DIR / "Cost Perishable.csv"
SALES_FILES   = [
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
PAX_FILES     = [
    DATA_DIR / "Passenger_Nat_Age_Seat-2024.csv",
    DATA_DIR / "Passenger_Nat_Age_Seat-2025.csv",
    DATA_DIR / "Passenger_Nat_Age_Seat-2026_Month5_24.csv",
]
PBM_FILES     = [
    DATA_DIR / "PBM-DATA_2024.csv",
    DATA_DIR / "PBM-DATA_2025.csv",
    DATA_DIR / "PBM-DATA_2026_Month1_4.csv",
    DATA_DIR / "PBM-DATA_2026_Month5_24.csv",
]
WATER_CODES   = {"BWFD", "BWAK", "BWHL", "WBHL"}

PAIR_FLIGHTS  = [175, 176]  # outbound + return

# Module-level caches — populated lazily, invalidated when actuals arrive
_pref_weights_cache = None   # {country: {sku: avg_units_per_pax}}
_monthly_nat_cache  = {}     # {month_int: {country: fraction}}

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
    cat_col = _col(df, "new_product_category")
    flt_col = _col(df, "flightnum")
    df = df[df[cat_col].str.strip().str.lower() == "perishable"].copy()
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
    pax_frames = []
    for fp in PAX_FILES:
        if fp.exists():
            pax_frames.append(pd.read_csv(fp, usecols=["FlightDate"], low_memory=False))
    if not pax_frames:
        return {}

    pax_df       = pd.concat(pax_frames, ignore_index=True)
    pax_per_date = pax_df.groupby("FlightDate").size().rename("total_pax")

    pbm_per_date = pd.Series(dtype=int, name="pbm_count")
    pbm_frames   = []
    for fp in PBM_FILES:
        if fp.exists():
            pbm_frames.append(pd.read_csv(fp, usecols=["FlightDate", "SSRCode"], low_memory=False))
    if pbm_frames:
        pbm_df       = pd.concat(pbm_frames, ignore_index=True)
        pbm_per_date = (pbm_df[~pbm_df["SSRCode"].isin(WATER_CODES)]
                        .groupby("FlightDate").size().rename("pbm_count"))

    merged = pax_per_date.to_frame().join(pbm_per_date, how="left").fillna(0)
    merged["net_bob"] = (merged["total_pax"] - merged["pbm_count"]).clip(lower=0).astype(int)
    return merged["net_bob"].to_dict()


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

    pax_frames = []
    for fp in PAX_FILES:
        if fp.exists():
            try:
                df = pd.read_csv(fp, usecols=["FlightDate", "UnitDesignator", "Country_name"],
                                 low_memory=False)
                df = df.rename(columns={"FlightDate": "date", "UnitDesignator": "seat",
                                        "Country_name": "country"})
                pax_frames.append(df)
            except Exception as e:
                print(f"[WARN] _build_preference_weights: failed to load {fp.name}: {e}")

    if not pax_frames:
        _pref_weights_cache = {}
        return {}

    pax_df = pd.concat(pax_frames, ignore_index=True)
    pax_df["date"]    = pd.to_datetime(pax_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
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

    pax_frames = []
    for fp in PAX_FILES:
        if fp.exists():
            try:
                df = pd.read_csv(fp, usecols=["FlightDate", "Country_name"], low_memory=False)
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

def _tobit_neg_ll(params, obs, caps):
    """Negative log-likelihood for censored normal (Tobit).
    obs: observed daily demand array
    caps: loaded quantity array (same length); np.inf if unknown
    """
    mu, log_sigma = params
    sigma = np.exp(log_sigma)
    if sigma < 1e-6:
        return 1e12
    uncensored = obs < caps
    ll = np.where(
        uncensored,
        norm.logpdf(obs, mu, sigma),
        np.log(np.maximum(1.0 - norm.cdf(caps, mu, sigma), 1e-15))
    ).sum()
    return -ll


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

    computed = {}
    results  = []

    # ── First pass: items WITH sales history ─────────────────────────────
    for item in active_items:
        code  = item["code"]
        proxy = item.get("proxy_code")
        theories = []

        item_sales = sales_df[sales_df[code_col].astype(str).str.strip() == code].copy()
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
            w_item = wastage_df[wastage_df[w_code_col].astype(str).str.strip() == code]
            if not w_item.empty:
                loaded_map = w_item.groupby(w_date_col)[w_open_col].sum().to_dict()
                daily["cap"] = daily["date"].map(loaded_map).fillna(np.inf)

        # Join historical net_bob; drop dates with no pax data
        daily["net_bob"] = daily["date"].map(net_bob_map).fillna(0).astype(int)
        daily = daily[daily["net_bob"] > 0].copy()
        if daily.empty:
            continue

        # Compute per-pax demand rate for each historical flight
        daily["rate"]     = daily["demand"] / daily["net_bob"]
        daily["cap_rate"] = daily.apply(
            lambda r: r["cap"] / r["net_bob"] if r["cap"] < np.inf else np.inf, axis=1
        )
        daily["censored"] = daily["rate"] >= daily["cap_rate"]
        daily["month"]    = pd.to_datetime(daily["date"]).dt.month
        n_censored_total  = int(daily["censored"].sum())

        # T2: Per-month Tobit MLE on demand rates
        # Discontinued months are absent from data — handled naturally (no special logic).
        monthly_params = {}
        for month_val, grp in daily.groupby("month"):
            obs_r = grp["rate"].values.astype(float)
            cap_r = grp["cap_rate"].values
            if len(obs_r) < 3:
                continue
            init_mu    = float(np.mean(obs_r))
            init_sigma = float(np.std(obs_r)) if np.std(obs_r) > 0 else 0.01
            try:
                res = minimize(
                    _tobit_neg_ll,
                    x0=[init_mu, np.log(max(init_sigma, 1e-6))],
                    args=(obs_r, cap_r),
                    method="Nelder-Mead",
                    options={"maxiter": 5000, "xatol": 1e-8, "fatol": 1e-8},
                )
                monthly_params[month_val] = (float(res.x[0]), float(np.exp(res.x[1])))
            except Exception:
                monthly_params[month_val] = (init_mu, max(init_sigma, 1e-4))

        # Global fallback rate (all months pooled — used when upcoming month has no history)
        all_rates = daily["rate"].values.astype(float)
        all_caps  = daily["cap_rate"].values
        init_mu_g    = float(np.mean(all_rates))
        init_sigma_g = float(np.std(all_rates)) if np.std(all_rates) > 0 else 0.01
        try:
            res_g = minimize(
                _tobit_neg_ll,
                x0=[init_mu_g, np.log(max(init_sigma_g, 1e-6))],
                args=(all_rates, all_caps),
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

        theories.append("T6:Substitution(skipped,established)")
        if any(ACTUALS_DIR.glob("sales_*.csv")):
            theories.append("T7:MLE-Refit(actuals_incorporated)")

        computed[code] = {"mu_rate": mu_rate, "sigma_rate": sigma_rate}

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
            flight_date = _extract_flight_date(pax_df)
        except Exception as e:
            return jsonify({"error": f"Failed to parse passenger CSV: {e}"}), 400

    if pbm_file:
        try:
            pbm_df = pd.read_csv(pbm_file, low_memory=False)
            pbm_date = _extract_flight_date(pbm_df)
        except Exception as e:
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
    """Accept actual post-flight sales + wastage CSVs.
    Appends to ACTUALS_DIR (permanent record), then re-runs Tobit MLE
    on the full updated dataset — this IS Theory 7 (MLE refit on combined dataset).
    """
    sales_file   = request.files.get("sales")
    wastage_file = request.files.get("wastage")

    if not sales_file and not wastage_file:
        return jsonify({"error": "Provide at least one file: sales or wastage"}), 400

    saved       = []
    flight_date = None

    if sales_file:
        try:
            df_sales    = pd.read_csv(sales_file, low_memory=False)
            flight_date = _extract_flight_date(df_sales)
            fname       = f"sales_{flight_date or 'unknown'}.csv"
            df_sales.to_csv(str(ACTUALS_DIR / fname), index=False)
            saved.append(fname)
        except Exception as e:
            return jsonify({"error": f"Failed to parse sales CSV: {e}"}), 400

    if wastage_file:
        try:
            df_wastage = pd.read_csv(wastage_file, low_memory=False)
            if not flight_date:
                flight_date = _extract_flight_date(df_wastage)
            fname = f"wastage_{flight_date or 'unknown'}.csv"
            df_wastage.to_csv(str(ACTUALS_DIR / fname), index=False)
            saved.append(fname)
        except Exception as e:
            return jsonify({"error": f"Failed to parse wastage CSV: {e}"}), 400

    # Invalidate preference weights so next forecast picks up the new actuals
    global _pref_weights_cache
    _pref_weights_cache = None

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
    """Return daily sales data from post-flight actuals uploads only."""
    frames = []
    for fp in sorted(ACTUALS_DIR.glob("sales_*.csv")):
        try:
            frames.append(pd.read_csv(fp, low_memory=False))
        except Exception:
            pass

    if not frames:
        return jsonify({"daily": [], "message": "No post-flight actuals uploaded yet"})

    df = pd.concat(frames, ignore_index=True)

    cat_col   = _col(df, "new_product_category")
    flt_col   = _col(df, "flightnum")
    code_col  = _col(df, "product_code")
    name_col  = _col(df, "product")
    qty_col   = _col(df, "quantity")
    price_col = _col(df, "product_price")
    date_col  = _col(df, "flight_date")

    df = df[df[cat_col].str.strip().str.lower() == "perishable"].copy()
    df = df[df[flt_col].isin(PAIR_FLIGHTS)].copy()

    df["_qty"] = pd.to_numeric(df[qty_col],   errors="coerce").fillna(0)
    df["_rev"] = pd.to_numeric(df[price_col], errors="coerce").fillna(0) * df["_qty"]

    daily = []
    for date_val, grp in df.groupby(date_col):
        products = []
        for code_val, pgrp in grp.groupby(code_col):
            products.append({
                "code":    str(code_val).strip(),
                "name":    str(pgrp[name_col].iloc[0]),
                "units":   int(pgrp["_qty"].sum()),
                "revenue": round(float(pgrp["_rev"].sum()), 2),
            })
        products.sort(key=lambda x: x["units"], reverse=True)
        daily.append({
            "date":          str(date_val),
            "total_units":   int(grp["_qty"].sum()),
            "total_revenue": round(float(grp["_rev"].sum()), 2),
            "products":      products,
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
