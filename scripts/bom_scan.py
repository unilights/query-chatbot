import pandas as pd
import os, sys

bom_dir = r"d:\unilights\query-chatbot\data\BOM-data_files"
files = sorted([f for f in os.listdir(bom_dir) if f.endswith('.xlsx')])
output = []

for fname in files[:10]:
    fpath = os.path.join(bom_dir, fname)
    try:
        # Try reading with no header to see raw rows
        df_raw = pd.read_excel(fpath, header=None)
        output.append(f"\n=== {fname} === Shape: {df_raw.shape}")
        output.append(df_raw.head(20).to_string())
    except Exception as e:
        output.append(f"ERROR {fname}: {e}")

with open(r"d:\unilights\query-chatbot\bom_schema_scan.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
print("Done")
