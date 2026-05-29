with open(r"C:\Users\Chaiwatwannawit\Desktop\AGY\dashboard.html", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, start=1):
        if "find" in line.lower() or "discover" in line.lower() or "insight" in line.lower():
            if len(line.strip()) < 150:
                print(f"Line {i}: {line.strip()}")
            else:
                print(f"Line {i}: {line.strip()[:150]}...")
