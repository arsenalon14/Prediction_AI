import csv
from collections import Counter

def check_gender():
    files = {
        '2024': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2024.csv",
        '2025': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2025.csv",
        '2026': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    }
    
    for year, file_path in files.items():
        genders = Counter()
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Find actual header casing
            for row in reader:
                g = row.get('gender', row.get('Gender', '')).strip()
                genders[g] += 1
        print(f"Year {year} gender distribution: {dict(genders)}")

if __name__ == "__main__":
    check_gender()
