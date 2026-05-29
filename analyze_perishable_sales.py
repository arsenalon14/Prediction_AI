import os
import csv
import sys
from collections import Counter, defaultdict

# Configure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

def analyze_perishables(file_path):
    print(f"\nAnalyzing Perishable Sales in: {file_path}")
    
    # Nested dictionary structure: Month (1-12) -> Product -> Statistics
    monthly_stats = defaultdict(lambda: defaultdict(lambda: {
        'quantity': 0,
        'revenue': 0.0,
        'transactions': 0
    }))
    
    global_product_totals = defaultdict(lambda: {
        'quantity': 0,
        'revenue': 0.0
    })
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Focus strictly on Perishables
                cat = row['product_category'].strip()
                if cat != 'Perishable':
                    continue
                
                date_str = row['flight_date'].strip()
                month = int(date_str.split('-')[1])
                
                product = row['product'].strip()
                
                # Parse quantity
                qty_str = row['quantity'].strip()
                qty = int(qty_str) if qty_str.isdigit() else 0
                
                # Parse net sales base (Revenue)
                rev_str = row['net_sales_base'].strip()
                rev = float(rev_str) if rev_str else 0.0
                
                # Exclude void/negative test entries if any (or include them to reflect true net sales)
                # Usually we want true net sales including discounts.
                
                # Record monthly stats
                monthly_stats[month][product]['quantity'] += qty
                monthly_stats[month][product]['revenue'] += rev
                monthly_stats[month][product]['transactions'] += 1
                
                # Record global totals
                global_product_totals[product]['quantity'] += qty
                global_product_totals[product]['revenue'] += rev
                
            except Exception as e:
                continue

    # 1. Print Global Product Rankings for the entire year
    print("\n" + "="*80)
    print(f"ANNUAL PERISHABLE SALES RANKING FOR {os.path.basename(file_path)}")
    print("="*80)
    sorted_global = sorted(global_product_totals.items(), key=lambda x: x[1]['quantity'], reverse=True)
    
    for i, (prod, stats) in enumerate(sorted_global, 1):
        safe_prod = prod.encode('ascii', errors='replace').decode('ascii')
        print(f"  {i:2d}. {safe_prod:<50} | Total Qty: {stats['quantity']:<6} | Total Net Rev: {stats['revenue']:,.2f} THB")

    # 2. Print Monthly Perishable Breakdown
    print("\n" + "="*80)
    print(f"MONTH-BY-MONTH PERISHABLE SALES & REVENUE REPORT")
    print("="*80)
    
    for month in sorted(monthly_stats.keys()):
        print(f"\n--- MONTH {month:02d} ---")
        month_products = monthly_stats[month]
        sorted_month_products = sorted(month_products.items(), key=lambda x: x[1]['quantity'], reverse=True)
        
        # Display top 5 items for this month
        for i, (prod, stats) in enumerate(sorted_month_products[:5], 1):
            safe_prod = prod.encode('ascii', errors='replace').decode('ascii')
            print(f"  {i}. {safe_prod:<45} | Qty: {stats['quantity']:<5} | Net Rev: {stats['revenue']:,.2f} THB")
            
        # Summary for the month
        m_total_qty = sum(p['quantity'] for p in month_products.values())
        m_total_rev = sum(p['revenue'] for p in month_products.values())
        print(f"  * MONTH TOTAL PERISHABLES SOLD: {m_total_qty} units | TOTAL NET REVENUE: {m_total_rev:,.2f} THB")

if __name__ == "__main__":
    # Run for 2025
    analyze_perishables(r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2025.csv")
