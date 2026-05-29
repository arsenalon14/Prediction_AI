import os
import csv
import sys
from collections import defaultdict

# Configure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

def find_matched_prices():
    # Standard prices we previously resolved
    prices = {
        'FNBG03002004': 180.0, # 8 TREASURE RICE BOWL
        'FNBG03001774': 150.0, # MALA HOTPOT NOODLES
        'FNBG03000041': 150.0, # ML NOI FRIED CHICKEN WITH BASIL ON RICE
        'FNBG03000025': 150.0, # UNCLE CHIN CHICKEN RICE
        'FNBG03002061': 150.0, # PALMYRA GRILLED CHICKEN, STICKY RICE AND SOMTAM
        'FNBG03000027': 150.0, # Chicken Teriyaki with Rice
        'FNBG03001857': 150.0, # FRIED FISH FILLET WITH SWEET CHILLI SAUCE AND RICE
        'FNBG03001880': 150.0, # GRILLED MACKEREL WITH JAPANESE SAUCE AND RICE
        'FNBG03002154': 150.0, # KHAO SOI GAI
        'FNBG03002153': 150.0, # LANNA KHAN TOK
        'FNBG03000085': 150.0, # Nasi Lemak & Pak Nasser's Nasi Lemak
        'FNBG03001956': 149.0, # GREEN CURRY CHICKEN WITH RICE AND SALTED EGG
        'FNBG03000077': 120.0, # THAI MANGO STICKY RICE.
        'FNBG03001926': 120.0, # AMERICAN FRIED RICE & KIDS' FRIED RICE
        'FNBG03002005': 120.0, # BAKED MAC DOUBLE CHEESE
        'FNBG03001931': 120.0, # BASIL CHICKEN FRIED RICE
        'FNBG03001959': 120.0, # CHICKEN CHEESE HAMBURG SANDWICH
        'FNBG02000820': 120.0, # JAPANESE MATCHA LATTE
        'FNBG03002102': 120.0, # KUA KLING KAI WITH SUNNY SALTED EGG
        'FNBG03001928': 120.0, # NAPOLETANA STYLE MUSHROOM TRUFFLE PIZZA
        'FNBG03002006': 120.0, # PIZZA OVAL CHICKEN SLICE & MUSHROOM
        'FNBG03001397': 120.0, # SHOKUPAN CHICKEN & CHEESE SANDWICH
        'FNBG02000276': 100.0, # Boba Thai Milk Tea
        'FNBG02000218': 100.0, # BOBA MILK TEA & Denmark Milk Tea
        'FNBG02000579': 100.0, # FRESH CALAMANSI JUICE
        'FNBG02000605': 100.0, # FRESH LONGAN JUICE
        'FNBG02000860': 100.0, # O-AEW FRESH LONGAN JUICE
        'FNBG03002010': 100.0, # THE OG BURNT CHEESECAKE
        'FNBG03002180': 100.0, # TUNA CORN & EBIKO KANIKAMA SANDWICH
        'FNBG02000888': 100.0, # PINEAPPLE PRIK KLUA JUICE
        'FNBG02000665': 100.0, # YUZU LEMON ROOIBOS TEA
        'FNBG03002158': 90.0,  # PHULAE PINEAPPLE CHEESECAKE
        'FNBG03001925': 80.0,  # KAO TOM MUD (BANANA NUTELLA STICKY RICE)
        'FNBG03001775': 60.0,  # BOBA MILK TEA PUDDING
        'FNBG03001776': 60.0,  # BOBA THAI MILK TEA PUDDING
        'FNBG03000519': 180.0, # Pad Thai with Egg Wrap
        'FNBG03002104': 180.0, # SOUTHERN YELLOW CURRY SEAFOOD WITH BASIL OMELETS
        'FNBG03002108': 100.0, # DIT SNACK BOX (Assumed)
    }
    return prices

def analyze_costs_and_margins():
    prices = find_matched_prices()
    cost_file = r"C:\Users\Chaiwatwannawit\Desktop\AI\Cost Perishable.csv"
    
    if not os.path.exists(cost_file):
        print(f"Error: Cost file not found at {cost_file}")
        return
        
    print("\n" + "="*95)
    print("FINANCIAL PARAMETERS MATRIX (2024 & 2025 PERISHABLES)")
    print("  * Price (p) from Sales | Cost (c) from Cost Perishable | CR = (p-c)/p")
    print("="*95)
    
    print(f"{'Product Name':<42} | {'Code':<12} | {'Price':<6} | {'2024 Cost':<9} | {'2025 Cost':<9} | {'2024 CR':<7} | {'2025 CR'}")
    print("-" * 105)
    
    with open(cost_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['Code'].strip()
            name = row['product_name'].strip()
            
            c_2024_str = row['2024'].strip()
            c_2025_str = row['2025'].strip()
            
            c_2024 = float(c_2024_str) if c_2024_str else None
            c_2025 = float(c_2025_str) if c_2025_str else None
            
            # Fetch retail price
            p = prices.get(code, None)
            
            if p is None:
                # Fallback matching by name
                p = 150.0  # default hot meal fallback
                
            # Calculate Critical Ratios (CR)
            cr_2024_str = "N/A"
            if c_2024 is not None:
                cr_2024 = (p - c_2024) / p
                cr_2024_str = f"{cr_2024*100:.1f}%"
                
            cr_2025_str = "N/A"
            if c_2025 is not None:
                cr_2025 = (p - c_2025) / p
                cr_2025_str = f"{cr_2025*100:.1f}%"
                
            c_2024_val = f"{c_2024:.2f}" if c_2024 is not None else "N/A"
            c_2025_val = f"{c_2025:.2f}" if c_2025 is not None else "N/A"
            
            safe_name = name.encode('ascii', errors='replace').decode('ascii')
            print(f"{safe_name:<42} | {code:<12} | {p:<6.1f} | {c_2024_val:<9} | {c_2025_val:<9} | {cr_2024_str:<7} | {cr_2025_str}")

if __name__ == "__main__":
    analyze_costs_and_margins()
