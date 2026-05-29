import csv

def find_unmatched_codes():
    search_codes = {'FNBG03002108', 'FNBG02000218', 'FNBG03000085'}
    found = {}
    
    sales_files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2024.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2025.csv"
    ]
    
    for file_path in sales_files:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['product_code'].strip()
                if code in search_codes:
                    price_str = row['product_price'].strip()
                    price = float(price_str) if price_str else 0.0
                    found[code] = {
                        'product': row['product'].strip(),
                        'price': price,
                        'category': row['product_category'].strip()
                    }
                    
    print("Found unmatched codes in sales:")
    for code, info in found.items():
        print(f"Code: {code} -> Product: '{info['product']}', Price: {info['price']}, Category: '{info['category']}'")

if __name__ == "__main__":
    find_unmatched_codes()
