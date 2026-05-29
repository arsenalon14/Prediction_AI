import csv
import numpy as np

def check_ages():
    files = {
        '2024': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2024.csv",
        '2025': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2025.csv",
        '2026': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    }
    
    for year, file_path in files.items():
        ages = []
        non_digit = []
        empty = 0
        negative = 0
        extreme = 0
        
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                val = row.get('PaxAge', row.get('Paxage', row.get('age', ''))).strip()
                if not val:
                    empty += 1
                elif not val.isdigit():
                    # Check negative
                    if val.startswith('-') and val[1:].isdigit():
                        negative += 1
                        ages.append(int(val))
                    else:
                        non_digit.append((idx, val))
                else:
                    age = int(val)
                    ages.append(age)
                    if age > 100 or age < 0:
                        extreme += 1
                        
        print(f"Year {year} age diagnostics:")
        print(f"  - Total records: {idx-1}")
        print(f"  - Empty ages: {empty}")
        print(f"  - Non-digit ages: {len(non_digit)} | Examples: {non_digit[:5]}")
        print(f"  - Negative ages: {negative}")
        print(f"  - Extreme ages (>100): {extreme}")
        if ages:
            print(f"  - Min: {min(ages)} | Max: {max(ages)} | Mean: {np.mean(ages):.2f} | Median: {np.median(ages)}")
            
if __name__ == "__main__":
    check_ages()
