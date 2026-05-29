"""Quick API test for the IFS-AI server."""
import requests
import json as js

BASE = "http://127.0.0.1:5000"

MOCK_DEMOGRAPHICS = {
    "total_pax": 200,
    "pbm_count": 30,
    "flight_date": "2026-06-15",
    "ages": {"adult": 170, "child": 30},
    "nationalities": {"TH": 120, "MV": 50, "Other": 30}
}

# 1) GET /api/menu
print("=== GET /api/menu ===")
r = requests.get(f"{BASE}/api/menu")
menu = r.json()
print(f"Status: {r.status_code}")
items = menu["items"]
print(f"Items: {len(items)}")
for it in items[:3]:
    print(f"  {it['code']} | {it['name'][:45]} | price={it['price']} cost={it['cost']} active={it['active']}")

# 2) POST /api/menu/toggle
print("\n=== POST /api/menu/toggle ===")
code0 = items[0]["code"]
r2 = requests.post(f"{BASE}/api/menu/toggle", json={"code": code0})
print(f"Status: {r2.status_code}")
toggled = r2.json()
print(f"  {toggled['items'][0]['code']} active={toggled['items'][0]['active']}")
requests.post(f"{BASE}/api/menu/toggle", json={"code": code0})

# 3a) POST /api/forecast — MUST return 400 without demographics
print("\n=== POST /api/forecast (no manifest — expect 400) ===")
r3_block = requests.post(f"{BASE}/api/forecast", json={})
print(f"Status: {r3_block.status_code}  {'PASS' if r3_block.status_code == 400 else 'FAIL — expected 400'}")
err_msg = r3_block.json().get("error", "")
print(f"  Error: {err_msg[:80]}")

# 3b) POST /api/forecast — with demographics, expect 200 + results
print("\n=== POST /api/forecast (with demographics) ===")
r3 = requests.post(f"{BASE}/api/forecast", json={"demographics": MOCK_DEMOGRAPHICS})
print(f"Status: {r3.status_code}  {'PASS' if r3.status_code == 200 else 'FAIL'}")
if r3.status_code == 200:
    results = r3.json()
    print(f"Results: {len(results)} items")
    for r_item in results:
        name = r_item["name"][:40].ljust(40)
        print(f"  {r_item['code']} | {name} | Q*={r_item['q_adjusted']:>3d} | "
              f"mu={r_item['mu']:.1f} sigma={r_item['sigma']:.1f} | "
              f"F*={r_item['critical_ratio']:.4f}")
        print(f"    Theories: {r_item['theories_applied']}")
else:
    print(f"  Error: {r3.json()}")

# 4) POST /api/menu/add (new item with proxy)
print("\n=== POST /api/menu/add ===")
r4 = requests.post(f"{BASE}/api/menu/add", json={
    "code": "FNBG99999999",
    "name": "TEST SEASONAL ITEM",
    "price": 100.0,
    "cost": 40.0,
    "proxy_code": "FNBG03000025"
})
print(f"Status: {r4.status_code}")
if r4.status_code == 201:
    added_menu = r4.json()
    print(f"  Total items now: {len(added_menu['items'])}")
    last = added_menu["items"][-1]
    print(f"  Added: {last['code']} proxy={last.get('proxy_code')}")

    # Run forecast with demographics to test Theory 6 proxy
    print("\n=== POST /api/forecast (proxy item — with demographics) ===")
    r5 = requests.post(f"{BASE}/api/forecast", json={"demographics": MOCK_DEMOGRAPHICS})
    if r5.status_code == 200:
        results2 = r5.json()
        proxy_result = [r for r in results2 if r["code"] == "FNBG99999999"]
        if proxy_result:
            pr = proxy_result[0]
            print(f"  Proxy item Q*={pr['q_adjusted']} mu={pr['mu']} sigma={pr['sigma']}")
            print(f"  Theories: {pr['theories_applied']}")
        else:
            print("  FAIL — proxy item not found in results")
    else:
        print(f"  FAIL — {r5.status_code}: {r5.json()}")

    # Clean up test item
    menu_path = r"C:\Users\Chaiwatwannawit\Desktop\AGY\active_menu.json"
    with open(menu_path, "r") as f:
        m = js.load(f)
    m["items"] = [i for i in m["items"] if i["code"] != "FNBG99999999"]
    with open(menu_path, "w") as f:
        js.dump(m, f, indent=2, ensure_ascii=False)
    print("  Cleaned up test item from menu.")

print("\n=== ALL TESTS DONE ===")
