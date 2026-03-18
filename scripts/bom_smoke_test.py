import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("=== BOM DATABASE LOAD ===")
from src.loaders.bom_loader import load_bom_database
db = load_bom_database()
print(f"Total rows: {len(db)}")
print(f"Unique products: {db['product_name'].nunique()}")
print(f"Columns: {list(db.columns)}")
print(f"\nSample products:\n{db['product_name'].unique()[:10]}")

print("\n=== TOOL: get_product_bom (SRDR12W-COB) ===")
from src.tools import get_product_bom
r = get_product_bom("SRDR12W-COB")
print(f"Found: {r['found']}")
if r['found']:
    print(f"Product: {r['product']}")
    print(f"Total cost INR: {r['total_manufacturing_cost_inr']}")
    print(f"Components: {r['total_components']}")
    print("Top 3 components:")
    for c in r['components'][:3]:
        print(f"  - {c['item']} | qty:{c['quantity']} | rate:{c['rate_inr']} | cost:{c['cost_inr']}")

print("\n=== TOOL: find_products_by_material (COB) ===")
from src.tools import find_products_by_material
r2 = find_products_by_material("COB")
print(f"Found: {r2['found']} | Products using COB: {r2.get('total_products', 0)}")

print("\n=== TOOL: compare_product_variants ===")
from src.tools import compare_product_variants
r3 = compare_product_variants("SRDR12W-COB", "SRDR15W-COB")
print(f"Found: {r3['found']}")
if r3['found']:
    print(f"Cost A: {r3['cost_a_inr']} | Cost B: {r3['cost_b_inr']} | Diff: {r3['cost_difference_inr']}")
