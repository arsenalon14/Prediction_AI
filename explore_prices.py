import os
import csv
import sys
from collections import Counter, defaultdict

# Configure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

def find_product_prices():
    print("Step 1: Loading unique products from Wastage files...")
    
    # Track unique products from wastage files
    # Key: product_name (standardized lower) -> {'name': original_name, 'prtnums': set()}
    wastage_products = defaultdict(lambda: {'name': None, 'prtnums': set(), 'records': 0})
    
    # Files to parse
    wastage_files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2024.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2025.csv"
    ]
    
    for file_path in wastage_files:
        if not os.path.exists(file_path):
            print(f"Warning: File not found {file_path}")
            continue
            
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    prod_name = row['product_name'].strip()
                    prtnum = row['prtnum'].strip()
                    
                    if not prod_name:
                        continue
                        
                    key = prod_name.lower()
                    if wastage_products[key]['name'] is None:
                        wastage_products[key]['name'] = prod_name
                    wastage_products[key]['prtnums'].add(prtnum)
                    wastage_products[key]['records'] += 1
                except Exception as e:
                    continue
                    
    print(f"Found {len(wastage_products)} unique products in Wastage data.")

    print("\nStep 2: Matching with Sales data to find product prices...")
    
    # Store prices found in sales
    # Key: product_name (standardized lower) -> set of (product_price, product_code)
    sales_info = defaultdict(lambda: {
        'prices': Counter(),
        'codes': Counter(),
        'categories': Counter()
    })
    
    sales_files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2024.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2025.csv"
    ]
    
    for file_path in sales_files:
        if not os.path.exists(file_path):
            print(f"Warning: File not found {file_path}")
            continue
            
        print(f"Scanning sales file: {os.path.basename(file_path)}...")
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    product = row['product'].strip()
                    if not product:
                        continue
                        
                    key = product.lower()
                    
                    # Parse price
                    price_str = row['product_price'].strip()
                    price = float(price_str) if price_str else 0.0
                    
                    code = row['product_code'].strip()
                    cat = row['product_category'].strip()
                    
                    sales_info[key]['prices'][price] += 1
                    if code:
                        sales_info[key]['codes'][code] += 1
                    if cat:
                        sales_info[key]['categories'][cat] += 1
                except Exception as e:
                    print(f"Error in row: {e}")
                    sys.exit(1)

    print("\n" + "="*80)
    print("PRODUCT PRICE MATCHING REPORT (WASTAGE vs. SALES)")
    print("="*80)
    
    matched_count = 0
    unmatched_count = 0
    
    matched_list = []
    unmatched_list = []
    
    for key, info in sorted(wastage_products.items()):
        original_name = info['name']
        prtnums = sorted(list(info['prtnums']))
        prtnums_str = ", ".join(prtnums)
        
        # Try exact or close matching in sales_info
        matched_info = None
        if key in sales_info:
            matched_info = sales_info[key]
        else:
            # Try matching by checking if the name exists in a different case or slightly altered
            # (sometimes punctuation or spaces differ)
            cleaned_key = key.replace('.', '').replace(',', '').strip()
            for s_key in sales_info.keys():
                cleaned_s_key = s_key.replace('.', '').replace(',', '').strip()
                if cleaned_key == cleaned_s_key:
                    matched_info = sales_info[s_key]
                    break
        
        if matched_info:
            matched_count += 1
            # Find most common price and code in sales
            most_common_price = matched_info['prices'].most_common(1)[0][0] if matched_info['prices'] else 0.0
            most_common_code = matched_info['codes'].most_common(1)[0][0] if matched_info['codes'] else "N/A"
            most_common_cat = matched_info['categories'].most_common(1)[0][0] if matched_info['categories'] else "N/A"
            
            matched_list.append({
                'name': original_name,
                'code_wastage': prtnums_str,
                'code_sales': most_common_code,
                'price': most_common_price,
                'category': most_common_cat
            })
        else:
            unmatched_count += 1
            unmatched_list.append({
                'name': original_name,
                'code_wastage': prtnums_str
            })
            
    # Print matched items
    print(f"\n[A] MATCHED PERISHABLE PRODUCTS ({matched_count} items):")
    for item in sorted(matched_list, key=lambda x: x['name']):
        safe_name = item['name'].encode('ascii', errors='replace').decode('ascii')
        print(f"  - {safe_name:<45} | Sales Code: {item['code_sales']:<12} | Price: {item['price']:<6.1f} | Cat: {item['category']}")
        
    # Print unmatched items if any
    if unmatched_list:
        print(f"\n[B] UNMATCHED PRODUCTS ({unmatched_count} items):")
        for item in sorted(unmatched_list, key=lambda x: x['name']):
            safe_name = item['name'].encode('ascii', errors='replace').decode('ascii')
            print(f"  - {safe_name:<45} | Wastage Code: {item['code_wastage']}")

if __name__ == "__main__":
    find_product_prices()
