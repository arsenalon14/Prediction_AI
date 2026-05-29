import csv

def check_dit():
    total_open = 0
    total_sales = 0
    records = 0
    
    wastage_files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2024.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2025.csv"
    ]
    
    for file_path in wastage_files:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prod = row['product_name'].strip()
                if 'DIT' in prod or 'dit' in prod.lower():
                    records += 1
                    total_open += int(row['open_quantity'])
                    total_sales += int(row['sale_quantity'])
                    
    print(f"DIT SNACK BOX: Records={records}, Loaded={total_open}, Sold={total_sales}")

if __name__ == "__main__":
    check_dit()
