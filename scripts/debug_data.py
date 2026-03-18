import pandas as pd
import os
from pathlib import Path

def debug_sheet(path, sheet_name, search_terms):
    if not os.path.exists(path):
        return f"File not found: {path}"
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
        cols = [c for c in df.columns if any(x.lower() in str(c).lower() for x in search_terms)]
        if not cols:
            cols = list(df.columns[:5])
        return df[cols].head(5).to_string()
    except Exception as e:
        return f"Error reading {sheet_name}: {e}"

output = []

# Check "Hold Orders" in PENDING SHEET 2
output.append("--- PENDING SHEET 2 - Hold Orders ---")
output.append(debug_sheet(r"data\orders\PENDING SHEET 2.xlsx", "Hold Orders", ["HBRR", "Qty", "Mech Store"]))

# Check "Sheet1" in Customization Orders
output.append("\n--- Customization Orders - Sheet1 ---")
output.append(debug_sheet(r"data\orders\Customization Orders FY 22-23.xlsx", "Sheet1", ["HBRR", "QTY", "Mech Store", "MODEL NAME"]))

with open(Path(__file__).parent / "output" / "debug_output.txt", "w") as f:
    f.write("\n".join(output))
print("Debug output written to scripts/output/debug_output.txt")
