import csv

def debug():
    # Print 5 rows of product names from wastage
    print("Wastage products:")
    with open(r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2024.csv", mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            print(f"  Name: '{row['product_name']}', Code: '{row['prtnum']}'")
            
    # Print 5 rows of product names from sales
    print("\nSales products:")
    with open(r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2024.csv", mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            print(f"  Name: '{row['product']}', Code: '{row['product_code']}', Price: '{row['product_price']}'")

if __name__ == "__main__":
    debug()
