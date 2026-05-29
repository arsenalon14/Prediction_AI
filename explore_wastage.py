import os
import csv
import sys
from collections import Counter, defaultdict

# Reconfigure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

def explore_wastage(file_path):
    print(f"\nStarting exploratory analysis of: {file_path}")
    
    total_rows = 0
    flights = Counter()
    products = Counter()
    
    # Aggregated metrics by Month (1-12) -> Product -> Stats
    monthly_stats = defaultdict(lambda: defaultdict(lambda: {
        'open_qty': 0,
        'sale_qty': 0,
        'wastage_qty': 0,
        'stockouts': 0,
        'total_flights': 0
    }))
    
    global_totals = defaultdict(lambda: {
        'open_qty': 0,
        'sale_qty': 0,
        'wastage_qty': 0,
        'stockouts': 0,
        'total_flights': 0
    })

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            
            flight = row['flightno'].strip()
            flights[flight] += 1
            
            product = row['product_name'].strip()
            products[product] += 1
            
            date_str = row['flightdate'].strip()
            try:
                month = int(date_str.split('-')[1])
            except:
                continue
                
            try:
                open_q = int(row['open_quantity'].strip())
                sale_q = int(row['sale_quantity'].strip())
                waste = int(row['wastage'].strip())
            except ValueError:
                # Handle potential non-numeric data
                continue
            
            # A stockout occurs if sold >= loaded (meaning demand was censored)
            is_stockout = 1 if sale_q >= open_q and open_q > 0 else 0
            
            # Monthly stats
            monthly_stats[month][product]['open_qty'] += open_q
            monthly_stats[month][product]['sale_qty'] += sale_q
            monthly_stats[month][product]['wastage_qty'] += waste
            monthly_stats[month][product]['stockouts'] += is_stockout
            monthly_stats[month][product]['total_flights'] += 1
            
            # Global totals
            global_totals[product]['open_qty'] += open_q
            global_totals[product]['sale_qty'] += sale_q
            global_totals[product]['wastage_qty'] += waste
            global_totals[product]['stockouts'] += is_stockout
            global_totals[product]['total_flights'] += 1

    print("\n" + "="*80)
    print(f"WASTAGE & CENSORING ANALYSIS FOR {os.path.basename(file_path)}")
    print("="*80)
    print(f"  * Total Data Records: {total_rows}")
    print(f"  * Unique Flights Listed: {dict(flights)}")
    
    # 1. Annual Product Performance & Wastage Ranking
    print("\n[1] ANNUAL PERISHABLE PERFORMANCE & WASTAGE RANKING:")
    sorted_global = sorted(global_totals.items(), key=lambda x: x[1]['open_qty'], reverse=True)
    
    for i, (prod, stats) in enumerate(sorted_global[:15], 1):
        safe_prod = prod.encode('ascii', errors='replace').decode('ascii')
        open_q = stats['open_qty']
        sale_q = stats['sale_qty']
        waste = stats['wastage_qty']
        stockouts = stats['stockouts']
        f_count = stats['total_flights']
        
        # Calculate rates
        sell_through_rate = (sale_q / open_q * 100) if open_q > 0 else 0.0
        stockout_rate = (stockouts / f_count * 100) if f_count > 0 else 0.0
        
        print(f"  {i:2d}. {safe_prod:<45} | Loaded: {open_q:<5} | Sold: {sale_q:<5} | Wasted: {waste:<5} | Sell-Through: {sell_through_rate:.1f}% | Stockout Rate: {stockout_rate:.1f}%")

    # 2. Monthly Summary (Wastage & Stockout Ratios)
    print("\n[2] MONTHLY TOTALS & SYSTEM PERFORMANCE:")
    for month in sorted(monthly_stats.keys()):
        month_products = monthly_stats[month]
        
        total_loaded = sum(p['open_qty'] for p in month_products.values())
        total_sold = sum(p['sale_qty'] for p in month_products.values())
        total_wasted = sum(p['wastage_qty'] for p in month_products.values())
        total_stockouts = sum(p['stockouts'] for p in month_products.values())
        total_records = sum(p['total_flights'] for p in month_products.values())
        
        m_sell_through = (total_sold / total_loaded * 100) if total_loaded > 0 else 0.0
        m_stockout_rate = (total_stockouts / total_records * 100) if total_records > 0 else 0.0
        
        print(f"  - Month {month:02d}: Loaded: {total_loaded:<5} | Sold: {total_sold:<5} | Wasted: {total_wasted:<5} | Sell-Through: {m_sell_through:.1f}% | Avg Stockout Rate: {m_stockout_rate:.1f}%")

if __name__ == "__main__":
    explore_wastage(r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2025.csv")
