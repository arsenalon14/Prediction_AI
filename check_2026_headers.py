import csv
import os

def check_2026_headers():
    files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2026_Month5_24.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month5_24.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2026_Month5_24.csv"
    ]
    
    print("Checking 2026 headers and row count...")
    for f_path in files:
        if not os.path.exists(f_path):
            print(f"File not found: {f_path}")
            continue
            
        with open(f_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            row_count = sum(1 for _ in reader)
            print(f"File: {os.path.basename(f_path)}")
            print(f"  - Rows: {row_count}")
            print(f"  - Columns: {headers}")

if __name__ == "__main__":
    check_2026_headers()
