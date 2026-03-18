"""
Step 1: Detect and display actual structure of 3 different BOM files
to understand exact row/column layout before building the parser.
"""
import pandas as pd
import os, sys

bom_dir = r"d:\unilights\query-chatbot\data\BOM-data_files"
out = []

# Pick 3 varied files
sample_files = [
    "SRDR12W-COB-BOM.xlsx",
    "SBDR-24W-BOM.xlsx",
    "NRRR08W-F- BOM.xlsx",
]

for fname in sample_files:
    fpath = os.path.join(bom_dir, fname)
    try:
        df = pd.read_excel(fpath, header=None)
        out.append(f"\n{'='*60}")
        out.append(f"FILE: {fname}  |  Shape: {df.shape}")
        out.append(f"{'='*60}")
        for i, row in df.iterrows():
            out.append(f"Row {i:2d}: {list(row.values)}")
    except Exception as e:
        out.append(f"ERROR {fname}: {e}")

with open(r"d:\unilights\query-chatbot\bom_raw_rows.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("DONE - rows written")
