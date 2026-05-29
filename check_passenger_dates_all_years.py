import csv
from collections import Counter

def check_dates_all():
    files = {
        '2024': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2024.csv",
        '2025': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2025.csv",
        '2026': r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    }
    
    for year, file_path in files.items():
        formats = Counter()
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                date = row.get('FlightDate', row.get('DATE', row.get('Date', ''))).strip()
                if '-' in date:
                    parts = date.split('-')
                    formats[f"Dash {len(parts[0])}-{len(parts[1])}-{len(parts[2])}"] += 1
                elif '/' in date:
                    parts = date.split('/')
                    formats[f"Slash {len(parts[0])}-{len(parts[1])}-{len(parts[2])}"] += 1
                else:
                    formats["Other"] += 1
                if i >= 1000:  # check first 1000 rows
                    break
        print(f"Year {year} date formats (sample): {dict(formats)}")

if __name__ == "__main__":
    check_dates_all()
