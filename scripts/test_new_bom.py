import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.loaders.bom_loader as bom_loader
bom_loader._BOM_DB = None

print("Loading BOM Database...")
db = bom_loader.load_bom_database()
print('\n=== DATABASE SUMMARY ===')
print(f'Total rows: {len(db)}')
print(f'Unique products/SKUs: {db["product_name"].nunique()}')
advanced = [p for p in db["product_name"].unique() if len(p) > 8 and any(c.isdigit() for c in p)]
print(f'Advanced-file products (e.g. variants like SRDR12F30T): {len(advanced)}')

from src.tools import get_product_bom, find_products_by_material, compare_product_variants

print('\n=== TOOL 9: get_product_bom (Base Product Search) ===')
r = get_product_bom('SRDR12W-COB')
print(f'Found: {r["found"]} | Matched: {r.get("product")} | Total cost: {r.get("total_manufacturing_cost_inr")}')

print('\n=== TOOL 9: get_product_bom (Specific SKU Search) ===')
r2 = get_product_bom('SRDR12F30T')
print(f'Found: {r2["found"]} | Matched: {r2.get("product")} | Total cost: {r2.get("total_manufacturing_cost_inr")}')

print('\n=== TOOL 11: compare_product_variants ===')
r4 = compare_product_variants('SRDR12F30T', 'SRDR15F30T')
print(f'Found: {r4["found"]}')
if r4["found"]:
    print(f'Cost A: {r4["cost_a_inr"]} | Cost B: {r4["cost_b_inr"]} | Diff: {r4["cost_difference_inr"]}')
    print('Key differences:')
    for diff in r4["items_with_differences"]:
        if abs(diff["cost_change_inr"]) > 1:
            print(f'  - {diff["item"][:40]}...: Diff Rs {diff["cost_change_inr"]}')
