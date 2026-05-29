import os
import csv
import sys
from collections import Counter, defaultdict

# Ensure standard output can print utf-8 characters on windows
sys.stdout.reconfigure(encoding='utf-8')

def explore_sales(file_path):
    print(f"Starting exploratory analysis of: {file_path}")
    
    total_rows = 0
    route_rows = 0
    categories = Counter()
    new_categories = Counter()
    brands = Counter()
    
    # Route specific counters (Flights 175 and 176)
    route_products = defaultdict(int)
    route_categories = Counter()
    route_monthly_sales = defaultdict(int)
    
    # Track unique products by category on DMK-MLE-DMK
    category_products = defaultdict(set)
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            
            flight = row['flightnum'].strip()
            origin = row['origin'].strip()
            dest = row['destination'].strip()
            
            cat = row['product_category'].strip()
            new_cat = row['new_product_category'].strip()
            brand = row['product_brand'].strip()
            
            categories[cat] += 1
            new_categories[new_cat] += 1
            if brand:
                brands[brand] += 1
                
            # Filter for DMK-MLE-DMK route flights (175 & 176)
            if flight in {'175', '176'}:
                route_rows += 1
                product_name = row['product'].strip()
                qty_str = row['quantity'].strip()
                qty = int(qty_str) if qty_str.isdigit() else 1
                
                route_products[product_name] += qty
                route_categories[cat] += 1
                
                date_str = row['flight_date']
                try:
                    month = int(date_str.split('-')[1])
                    route_monthly_sales[month] += qty
                except:
                    pass
                
                if cat:
                    category_products[cat].add(product_name)

    print("\n" + "="*80)
    print(f"EXPLORATORY DATA ANALYSIS FOR {os.path.basename(file_path)}")
    print("="*80)
    print(f"  * Total Transactions in File: {total_rows}")
    print(f"  * Transactions on DMK-MLE-DMK (175/176): {route_rows} ({route_rows/total_rows*100:.2f}%)")
    
    print("\n[1] GLOBAL CATEGORY DISTRIBUTION (ALL FLIGHTS IN CSV):")
    for cat, count in categories.most_common():
        print(f"  - {cat if cat else 'Empty'}: {count} ({count/total_rows*100:.2f}%)")
        
    print("\n[2] DMK-MLE-DMK SPECIFIC CATEGORY DISTRIBUTION:")
    for cat, count in route_categories.most_common():
        pax_p_count = len(category_products[cat])
        print(f"  - {cat if cat else 'Empty'}: {count} transactions | {pax_p_count} unique items")

    print("\n[3] DMK-MLE-DMK TOP 15 BEST-SELLING PRODUCTS (BY TOTAL QUANTITY SOLD):")
    top_products = Counter(route_products).most_common(15)
    for i, (prod, qty) in enumerate(top_products, 1):
        # Find which category this product belongs to
        prod_cat = "Unknown"
        for c, prods in category_products.items():
            if prod in prods:
                prod_cat = c
                break
        print(f"  {i:2d}. {prod:<55} | Qty: {qty:<6} | Cat: {prod_cat}")

    print("\n[4] DMK-MLE-DMK MONTHLY SALES VOLUME PROFILE:")
    for month in sorted(route_monthly_sales.keys()):
        print(f"  - Month {month:02d}: {route_monthly_sales[month]} items sold")
        
    print("\n[5] DETAILED ITEM LIST BY CATEGORY ON DMK-MLE-DMK:")
    for cat, prods in category_products.items():
        print(f"  * Category '{cat}' has {len(prods)} unique items:")
        sorted_prods = sorted(list(prods))[:10]  # Show top 10 items alphabetically
        for p in sorted_prods:
            # Safely encode/decode to avoid printing errors on windows
            safe_p = p.encode('ascii', errors='replace').decode('ascii')
            print(f"    - {safe_p}")
        if len(prods) > 10:
            print(f"    ... and {len(prods)-10} more items.")

if __name__ == "__main__":
    explore_sales(r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2024.csv")
