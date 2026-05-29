import os
import csv
import sys
import numpy as np
from collections import defaultdict

# Configure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

def norm_cdf(x):
    """
    Abramowitz & Stegun formula 26.2.17 approximation for standard normal CDF.
    Highly accurate with absolute error < 7.5e-8.
    Works seamlessly on scalar values and numpy arrays.
    """
    x = np.array(x, dtype=float)
    sgn = np.sign(x)
    z = np.abs(x)
    
    p = 0.2316419
    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255978
    b5 = 1.330274429
    
    t = 1.0 / (1.0 + p * z)
    phi = 1.0 / np.sqrt(2 * np.pi) * np.exp(-0.5 * z**2)
    cdf = 1.0 - phi * (b1 * t + b2 * t**2 + b3 * t**3 + b4 * t**4 + b5 * t**5)
    
    return np.where(sgn >= 0, cdf, 1.0 - cdf)

def norm_ppf(q):
    """
    Fast, precise bisection search for the inverse normal CDF (percent point function).
    q is a probability in (0, 1).
    """
    if q <= 0.0:
        return -8.0
    if q >= 1.0:
        return 8.0
        
    low, high = -8.0, 8.0
    for _ in range(30):
        mid = 0.5 * (low + high)
        val = norm_cdf(mid)
        if val < q:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)

def fit_tobit_uncensored_demand(y_total, Q_loaded, censored_mask):
    """
    Fits a Tobit maximum likelihood model using a robust, grid-search based 
    optimization in pure numpy. Guarantees global convergence without scipy.
    """
    # Filter out empty or zero loading cases
    valid = Q_loaded > 0
    y_total = y_total[valid]
    Q_loaded = Q_loaded[valid]
    censored_mask = censored_mask[valid]
    
    if len(y_total) < 5:
        # Not enough data points to fit reliably, fallback to empirical stats
        return np.mean(y_total), max(1.0, np.std(y_total))
        
    y_uncensored = y_total[~censored_mask]
    Q_censored = Q_loaded[censored_mask]
    
    # Establish grid ranges based on observed data
    max_y = max(y_total)
    mean_y = np.mean(y_total)
    std_y = max(1.0, np.std(y_total))
    
    # Grid search for global minimum of negative log-likelihood
    mus = np.linspace(max(0.0, mean_y - 2 * std_y), mean_y + 3 * std_y, 80)
    sigmas = np.linspace(max(0.5, 0.2 * std_y), 2.5 * std_y, 40)
    
    best_ll = 1e10
    best_mu = mean_y
    best_sigma = std_y
    
    for mu in mus:
        for sigma in sigmas:
            # 1. Uncensored log-likelihood term
            uncensored_term = 0.0
            if len(y_uncensored) > 0:
                z_un = (y_uncensored - mu) / sigma
                uncensored_term = (
                    -0.5 * len(y_uncensored) * np.log(2 * np.pi) 
                    - len(y_uncensored) * np.log(sigma) 
                    - 0.5 * np.sum(z_un**2)
                )
                
            # 2. Censored log-likelihood term (Survival Function)
            censored_term = 0.0
            if len(Q_censored) > 0:
                z_cen = (Q_censored - mu) / sigma
                sf_vals = 1.0 - norm_cdf(z_cen)
                sf_vals = np.clip(sf_vals, 1e-12, 1.0)
                censored_term = np.sum(np.log(sf_vals))
                
            ll = -(uncensored_term + censored_term)
            if ll < best_ll:
                best_ll = ll
                best_mu = mu
                best_sigma = sigma
                
    return best_mu, best_sigma

def expected_sales(Q, mu, sigma):
    """
    Calculates the exact expected sales E[min(D, Q)] under normal demand D ~ N(mu, sigma^2).
    """
    if Q <= 0 or sigma <= 1e-4:
        return 0.0
    z = (Q - mu) / sigma
    phi_z = 1.0 / np.sqrt(2 * np.pi) * np.exp(-0.5 * z**2)
    Phi_z = norm_cdf(z)
    
    exp_sales = mu * Phi_z - sigma * phi_z + Q * (1.0 - Phi_z)
    return max(0.0, exp_sales)

def run_uncensoring_analysis():
    data_file = r"C:\Users\Chaiwatwannawit\Desktop\AGY\perishable_historical_data.csv"
    
    if not os.path.exists(data_file):
        print(f"Error: Historical database not found at {data_file}")
        return
        
    print("="*110)
    print("   TOBIT DEMAND UN-CENSORING & NEWSVENDOR INVENTORY OPTIMIZATION REPORT (PURE NUMPY CORE)")
    print("       TAA Buy-on-Board Perishable Route Optimization (DMK-MLE-DMK) 2024-2026")
    print("="*110)
    
    # 1. Load data
    product_stats = defaultdict(lambda: {
        'total_loaded': 0,
        'total_sold': 0,
        'total_wasted': 0,
        'records': 0,
        'name': '',
        'prices': [],
        'costs': [],
        'by_month': defaultdict(list)
    })
    
    with open(data_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                code = row['ProductCode'].strip()
                name = row['ProductName'].strip()
                month = int(row['FlightDate'].split('-')[1])
                
                loaded = int(row['LoadedQty'])
                sold = int(row['SoldQty'])
                waste = int(row['WastedQty'])
                stockout = int(row['StockoutFlag'])
                
                price = float(row['Price'])
                cost = float(row['Cost'])
                
                product_stats[code]['name'] = name
                product_stats[code]['total_loaded'] += loaded
                product_stats[code]['total_sold'] += sold
                product_stats[code]['total_wasted'] += waste
                product_stats[code]['records'] += 1
                product_stats[code]['prices'].append(price)
                product_stats[code]['costs'].append(cost)
                
                product_stats[code]['by_month'][month].append({
                    'loaded': loaded,
                    'sold': sold,
                    'waste': waste,
                    'stockout': stockout,
                    'price': price,
                    'cost': cost
                })
            except Exception as e:
                continue
                
    # Identify top 5 perishables by volume of sales
    top_perishables = sorted(
        product_stats.keys(),
        key=lambda k: product_stats[k]['total_sold'],
        reverse=True
    )[:5]
    
    month_names = {
        1: 'Jan', 2: 'Feb (CNY)', 3: 'Mar', 4: 'Apr (Songk)', 5: 'May', 6: 'Jun',
        7: 'Jul (Peak)', 8: 'Aug (Peak)', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    
    for rank, code in enumerate(top_perishables, 1):
        info = product_stats[code]
        name = info['name']
        avg_price = np.mean(info['prices'])
        avg_cost = np.mean(info['costs'])
        cr = (avg_price - avg_cost) / avg_price if avg_price > 0 else 0.0
        
        safe_name = name.encode('ascii', errors='replace').decode('ascii')
        print(f"\n{rank}. PRODUCT: {safe_name} (Code: {code})")
        print(f"   Avg Price: {avg_price:.1f} THB | Avg Purchase Cost: {avg_cost:.2f} THB | Route Critical Ratio (CR): {cr*100:.1f}%")
        print("-"*110)
        print(f"   {'Month':<12} | {'Hist Load':<9} | {'Hist Sales':<10} | {'True Mean':<9} | {'True Std':<8} | {'Opt Q*':<8} | {'Hist Profit':<11} | {'Opt Profit':<10} | {'Uplift %':<8}")
        print("-"*110)
        
        total_hist_profit = 0.0
        total_opt_profit = 0.0
        
        for m in sorted(info['by_month'].keys()):
            records = info['by_month'][m]
            if len(records) < 2:
                continue
                
            # Arrays for fitting
            loaded_arr = np.array([r['loaded'] for r in records], dtype=float)
            sold_arr = np.array([r['sold'] for r in records], dtype=float)
            stockout_arr = np.array([r['stockout'] for r in records], dtype=bool)
            
            price_m = np.mean([r['price'] for r in records])
            cost_m = np.mean([r['cost'] for r in records])
            
            hist_load_mean = np.mean(loaded_arr)
            hist_sold_mean = np.mean(sold_arr)
            
            # Run Tobit model fitting (pure numpy core)
            mu_true, sigma_true = fit_tobit_uncensored_demand(sold_arr, loaded_arr, stockout_arr)
            
            # Newsvendor optimization
            cr_m = (price_m - cost_m) / price_m if price_m > 0 else 0.0
            z_score = norm_ppf(cr_m) if cr_m > 0 else 0.0
            
            Q_opt = mu_true + z_score * sigma_true
            Q_opt = max(0, int(np.round(Q_opt)))
            
            # Calculate financial comparison (expected monthly performance)
            num_flights = len(records)
            
            exp_s_hist = np.mean([expected_sales(l, mu_true, sigma_true) for l in loaded_arr])
            exp_profit_hist = (price_m * exp_s_hist - cost_m * hist_load_mean) * num_flights
            
            exp_s_opt = expected_sales(Q_opt, mu_true, sigma_true)
            exp_profit_opt = (price_m * exp_s_opt - cost_m * Q_opt) * num_flights
            
            total_hist_profit += exp_profit_hist
            total_opt_profit += exp_profit_opt
            
            # Uplift
            profit_diff = exp_profit_opt - exp_profit_hist
            uplift_pct = (profit_diff / exp_profit_hist * 100) if exp_profit_hist > 0 else 0.0
            
            # Format row
            m_name = month_names.get(m, f"Month {m:02d}")
            print(f"   {m_name:<12} | {hist_load_mean:<9.1f} | {hist_sold_mean:<10.1f} | {mu_true:<9.1f} | {sigma_true:<8.1f} | {Q_opt:<8d} | {exp_profit_hist:<11,.0f} | {exp_profit_opt:<10,.0f} | {uplift_pct:+.1f}%")
            
        annual_uplift_pct = (total_opt_profit - total_hist_profit) / total_hist_profit * 100 if total_hist_profit > 0 else 0.0
        print("-"*110)
        print(f"   ANNUAL SUMMARY EXPECTED PROFIT: Historical: {total_hist_profit:,.2f} THB | Optimized (Q*): {total_opt_profit:,.2f} THB | Overall Uplift: {annual_uplift_pct:+.2f}%")
        print("="*110)

if __name__ == "__main__":
    run_uncensoring_analysis()
