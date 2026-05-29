import csv
import re
from collections import Counter

def inspect_pax_dates():
    file_path = r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    
    non_standard_dates = []
    headers = []
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            print("Empty file")
            return
            
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        for idx, row in enumerate(reader, start=2):
            if not row:
                continue
            date_val = row[0].strip()
            if not date_pattern.match(date_val):
                non_standard_dates.append((idx, date_val))
                
    print(f"Total Rows Checked: {idx}")
    print(f"Header row: {headers}")
    print(f"Number of non-standard dates: {len(non_standard_dates)}")
    if non_standard_dates:
        print("First 20 non-standard dates:")
        for r_num, val in non_standard_dates[:20]:
            print(f"  - Line {r_num}: '{val}'")
            
if __name__ == "__main__":
    inspect_pax_dates()
