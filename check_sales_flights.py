import csv
import os
from collections import Counter

def check_sales_flights():
    sales_files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month5_24.csv"
    ]
    
    for file_path in sales_files:
        if not os.path.exists(file_path):
            continue
        flights = Counter()
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                flight = row.get('flightnum', '').strip()
                flights[flight] += 1
        print(f"File: {os.path.basename(file_path)} flight numbers: {dict(flights)}")

if __name__ == "__main__":
    check_sales_flights()
