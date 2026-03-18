import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force reload singleton
import src.loaders.bom_loader as bom_loader
bom_loader._BOM_DB = None

from src.tools import get_product_bom, calculate_batch_materials

print("=== SRDR12W-COB BOM Cost (Expected: ~Rs. 146.33) ===")
r = get_product_bom("SRDR12W-COB")
print(f"Found: {r['found']}")
if r['found']:
    print(f"Product: {r['product']}")
    print(f"Total Manufacturing Cost (INR): Rs. {r['total_manufacturing_cost_inr']}")
    print(f"\nAll components with cost:")
    for c in r['components']:
        print(f"  {c['item']:<55} qty:{str(c['quantity']):<6} rate:{str(c['rate_inr']):<10} cost_inr:{c['cost_inr']}")

print("\n=== BATCH PLAN: 100 units SRDR12W-COB ===")
b = calculate_batch_materials([{"model": "SRDR12W-COB", "quantity": 100}])
print(f"Grand Total (INR): Rs. {b['grand_total_cost_inr']}")
print(f"Expected: Rs. {round(146.33 * 100, 2)}")
