import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.loaders.order_loader import load_all_data
from src.config import DATA_DIR

dfs = load_all_data(str(DATA_DIR))
out = []

# 1. Find all customer name variations that contain JR/ELECTRO
out.append("=== CUSTOMER NAME VARIATIONS (JR/ELECTRO) ===")
seen = set()
for name, df in dfs.items():
    cust_cols = [c for c in df.columns if any(x in str(c).lower() for x in ["customer", "client"])]
    for col in cust_cols:
        vals = df[col].dropna().astype(str).str.strip().unique()
        for v in vals:
            if any(x in v.upper() for x in ["JR", "ELECTRO", "ELCTRO", "J.R"]):
                if v not in seen:
                    out.append(f"  Sheet: [{name}]  Column: [{col}]  Value: '{v}'")
                    seen.add(v)

# 2. Check GLWR18W 35K - is customer name there?
out.append("\n=== GLWR18W 35K - Does it have a Customer column? ===")
for name, df in dfs.items():
    model_cols = [c for c in df.columns if any(x in str(c).lower() for x in ["model", "product"])]
    cust_cols = [c for c in df.columns if any(x in str(c).lower() for x in ["customer", "client"])]
    for mc in model_cols:
        rows = df[df[mc].astype(str).str.contains("GLWR18W", case=False, na=False)]
        if not rows.empty:
            out.append(f"  Found in sheet: {name}")
            for cc in cust_cols:
                out.append(f"    [{cc}]: {rows[cc].tolist()}")
            if not cust_cols:
                out.append(f"    No customer column found. Columns available: {list(df.columns)}")

# Write to output
with open(Path(__file__).parent / "output" / "debug_customers.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("DONE")
