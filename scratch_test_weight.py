import pandas as pd
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
import math

from app import _load_sales, _load_net_bob_history, _load_wastage, _col

sales_df = _load_sales()
wastage_df = _load_wastage()
net_bob_map = _load_net_bob_history()

code_col = _col(sales_df, 'product_code')
qty_col  = _col(sales_df, 'quantity')
date_col = _col(sales_df, 'flight_date')

w_code_col = _col(wastage_df, 'prtnum') if not wastage_df.empty else None
w_date_col = _col(wastage_df, 'flightdate') if not wastage_df.empty else None
w_open_col = _col(wastage_df, 'open_quantity') if not wastage_df.empty else None

def _tobit_neg_ll(params, obs, caps, weights=None):
    mu, log_sigma = params
    sigma = np.exp(log_sigma)
    if sigma < 1e-6:
        return 1e12
    uncensored = obs < caps
    terms = np.where(
        uncensored,
        norm.logpdf(obs, mu, sigma),
        np.log(np.maximum(1.0 - norm.cdf(caps, mu, sigma), 1e-15))
    )
    if weights is not None:
        terms = terms * weights
    return -terms.sum()

# Let's run a comparison for ML NOI and Palmyra for June 12
# With Weighting = 10.0 for actuals, and 1.0 for historical
# Net BoB up = 167

net_bob_up = 167
upcoming_month = 6
from pathlib import Path
ACTUALS_DIR = Path('uploads/actuals')
actuals_dates = {fp.stem.replace('sales_', '') for fp in ACTUALS_DIR.glob('sales_*.csv')}

for weight_factor in [1.0, 5.0, 10.0]:
    print(f"\n--- Weight Factor for Recent Actuals: {weight_factor} ---")
    for code in ['FNBG03000041', 'FNBG03002061']:
        item_sales = sales_df[sales_df[code_col].astype(str).str.strip() == code].copy()
        daily = (item_sales.groupby(date_col)[qty_col]
                 .sum().reset_index()
                 .rename(columns={date_col: 'date', qty_col: 'demand'}))
        
        daily['cap'] = np.inf
        if not wastage_df.empty and w_code_col:
            w_item = wastage_df[wastage_df[w_code_col].astype(str).str.strip() == code]
            if not w_item.empty:
                loaded_map = w_item.groupby(w_date_col)[w_open_col].sum().to_dict()
                daily['cap'] = daily['date'].map(loaded_map).fillna(np.inf)
                
        daily['net_bob'] = daily['date'].map(net_bob_map).fillna(0).astype(int)
        daily = daily[daily['net_bob'] > 0].copy()
        
        daily['rate'] = daily['demand'] / daily['net_bob']
        daily['cap_rate'] = daily.apply(lambda r: r['cap'] / r['net_bob'] if r['cap'] < np.inf else np.inf, axis=1)
        daily['censored'] = daily['rate'] >= daily['cap_rate']
        daily['month'] = pd.to_datetime(daily['date']).dt.month
        daily['weight'] = daily['date'].apply(lambda d: weight_factor if d in actuals_dates else 1.0)
        
        # Filter to month 6 (June)
        grp = daily[daily['month'] == upcoming_month]
        obs_r = grp['rate'].values.astype(float)
        cap_r = grp['cap_rate'].values
        obs_w = grp['weight'].values.astype(float)
        
        init_mu = float(np.mean(obs_r))
        init_sigma = float(np.std(obs_r)) if np.std(obs_r) > 0 else 0.01
        
        res = minimize(
            _tobit_neg_ll,
            x0=[init_mu, np.log(max(init_sigma, 1e-6))],
            args=(obs_r, cap_r, obs_w),
            method='Nelder-Mead',
            options={'maxiter': 5000, 'xatol': 1e-8, 'fatol': 1e-8}
        )
        mu_rate, sigma_rate = float(res.x[0]), float(np.exp(res.x[1]))
        
        # Newsvendor parameters
        price, cost = (180.0, 46.5) if code == 'FNBG03000041' else (180.0, 56.0)
        C_o = cost
        C_u = price - cost
        F_star = C_u / (C_u + C_o)
        z = float(norm.ppf(F_star))
        
        mu_flight = mu_rate * net_bob_up
        sigma_flight = sigma_rate * net_bob_up
        q_newsvendor = max(mu_flight + z * sigma_flight, 0)
        q_baseline = math.ceil(q_newsvendor)
        
        print(f"SKU: {code} | mu_rate={mu_rate:.4f} | sigma_rate={sigma_rate:.4f} | expected mu={mu_flight:.1f} | Q*={q_baseline}")
