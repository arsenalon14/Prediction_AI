import os
import csv
import numpy as np
from collections import defaultdict
from scipy.optimize import minimize
import scipy.stats as stats
import warnings

warnings.filterwarnings("ignore")

def load_costs(filepath):
    costs = {}
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['Code'].strip()
            if not code: continue
            
            # Prefer 2026, fallback to 2025
            c = row.get('2026', '').strip()
            if not c: c = row.get('2025', '').strip()
            if not c: c = row.get('2024', '').strip()
            
            if c:
                try:
                    costs[code] = float(c)
                except:
                    pass
    return costs

def get_date(row, cols):
    for c in cols:
        if c in row and row[c]:
            return row[c].strip()
    return list(row.values())[0].strip() # fallback to first col

def parse_data(base_dir):
    costs = load_costs(os.path.join(base_dir, "Cost Perishable.csv"))
    
    # We will use 2026 data to form the most current prediction baseline
    w_files = [
        os.path.join(base_dir, "Wastage-2026_Month1_4.csv"),
        os.path.join(base_dir, "Wastage-2026_Month5_24.csv")
    ]
    s_files = [
        os.path.join(base_dir, "SaleALL2026_Month1_4.csv"),
        os.path.join(base_dir, "SaleALL2026_Month5_24.csv")
    ]
    
    # Store data: dict[product_code][date] = {'sales': 0, 'loaded': 0, 'revenue': 0, 'name': ''}
    data = defaultdict(lambda: defaultdict(lambda: {'sales': 0, 'loaded': 0, 'revenue': 0, 'name': ''}))
    perishable_codes = set()
    
    # 1. Parse Sales (Pair-Route Aggregation)
    for sf in s_files:
        if not os.path.exists(sf): continue
        with open(sf, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat = row.get('product_category', row.get('new_product_category', '')).strip()
                # STRICT FILTER: Only 'Perishable' category
                if cat.lower() != 'perishable':
                    continue
                    
                date = get_date(row, ['flight_date', 'transaction_date'])
                code = row.get('product_code', '').strip()
                name = row.get('product', '').strip()
                qty = float(row['quantity']) if row.get('quantity') else 1.0
                rev = float(row['net_sales_base']) if row.get('net_sales_base') else 0.0
                
                if code:
                    data[code][date]['sales'] += qty
                    data[code][date]['revenue'] += rev
                    data[code][date]['name'] = name
                    perishable_codes.add(code)
                    
    # 2. Parse Wastage (Loaded Capacity)
    for wf in w_files:
        if not os.path.exists(wf): continue
        with open(wf, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = get_date(row, ['flightdate'])
                code = row.get('prtnum', '').strip()
                
                if code in perishable_codes:
                    loaded = float(row.get('open_quantity', 0))
                    data[code][date]['loaded'] = loaded
                    if not data[code][date]['name']:
                        data[code][date]['name'] = row.get('product_name', '')
                        
    return data, costs

def fit_uncensored_demand(y_total, Q_loaded, censored_mask):
    def log_likelihood(params):
        mu, sigma = params
        if sigma <= 0.1: return 1e10
        
        # Uncensored
        uncensored_y = y_total[~censored_mask]
        pdf_term = stats.norm.logpdf(uncensored_y, loc=mu, scale=sigma)
        
        # Censored
        censored_Q = Q_loaded[censored_mask]
        sf_term = stats.norm.logsf(censored_Q, loc=mu, scale=sigma)
        
        # Guard against -inf
        pdf_term = np.clip(pdf_term, -1e5, 1e5)
        sf_term = np.clip(sf_term, -1e5, 1e5)
        
        return -(np.sum(pdf_term) + np.sum(sf_term))

    init_mu = np.mean(y_total) if len(y_total) > 0 else 0
    init_sigma = np.std(y_total) if len(y_total) > 0 and np.std(y_total) > 0 else 1.0
    
    res = minimize(log_likelihood, x0=[init_mu, init_sigma], method='Nelder-Mead', options={'maxiter': 1000})
    if res.success:
        return res.x[0], res.x[1]
    return init_mu, init_sigma # Fallback if fails to converge

def main():
    base_dir = r"C:\Users\Chaiwatwannawit\Desktop\AI"
    data, costs = parse_data(base_dir)
    
    results = []
    
    for code, date_dict in data.items():
        name = ""
        y_total = []
        Q_loaded = []
        revenues = []
        
        for date, metrics in date_dict.items():
            if not name and metrics['name']: name = metrics['name']
            
            s = metrics['sales']
            l = metrics['loaded']
            r = metrics['revenue']
            
            # We must have a load record to know censoring
            if l > 0:
                y_total.append(s)
                Q_loaded.append(l)
                if s > 0: revenues.append(r / s)
                
        if len(y_total) < 10:
            continue # Skip items with very little data
            
        y_total = np.array(y_total)
        Q_loaded = np.array(Q_loaded)
        
        # Censoring Detection
        censored_mask = y_total >= Q_loaded
        stockout_rate = np.mean(censored_mask) * 100
        
        # Run Tobit
        mu, sigma = fit_uncensored_demand(y_total, Q_loaded, censored_mask)
        
        # Financials
        avg_price = np.mean(revenues) if len(revenues) > 0 else 100.0
        cost = costs.get(code, None)
        if cost is None:
            continue # Cannot optimize without cost
            
        # Newsvendor Optimization
        C_u = avg_price - cost
        C_o = cost
        critical_ratio = C_u / (C_u + C_o)
        
        z = stats.norm.ppf(critical_ratio)
        Q_opt = max(0, int(np.round(mu + z * sigma)))
        
        # Historical metrics
        hist_load = np.mean(Q_loaded)
        
        results.append({
            'code': code,
            'name': name,
            'price': avg_price,
            'cost': cost,
            'cr': critical_ratio * 100,
            'stockout': stockout_rate,
            'mu': mu,
            'hist_load': hist_load,
            'q_opt': Q_opt
        })
        
    # Sort by Optimized Q*
    results.sort(key=lambda x: x['q_opt'], reverse=True)
    
    print("=======================================================================================================================")
    print("                          AI PAIR-ROUTE PERISHABLE FORECAST (BASELINE Q*)                                              ")
    print("=======================================================================================================================")
    print(f"{'Product Name':<35} | {'Price':<6} | {'Cost':<5} | {'CR%':<5} | {'Stockout':<8} | {'Avg Demand':<10} | {'Hist Load':<9} | {'Optimal Q*':<10}")
    print("-" * 115)
    
    for r in results:
        name = r['name'][:34]
        print(f"{name:<35} | {r['price']:<6.0f} | {r['cost']:<5.0f} | {r['cr']:<4.1f}% | {r['stockout']:<7.1f}% | {r['mu']:<10.1f} | {r['hist_load']:<9.1f} | {r['q_opt']:<10}")
        
if __name__ == '__main__':
    main()
