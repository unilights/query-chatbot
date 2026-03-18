import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tools import get_all_products_list, get_hold_orders, get_orders_summary, get_product_summary

print("=== Products List ===")
r = get_all_products_list()
print("Found", r["total_products"], "products")
print("First 5:", r["products"][:5])

print("\n=== Summary ===")
s = get_orders_summary()
print(s["summary"])

print("\n=== Hold Orders ===")
h = get_hold_orders()
print("Found:", h["found"], "| Total:", h.get("total", 0))

print("\n=== Product Summary: TTLB24W 35K ===")
p = get_product_summary("TTLB24W 35K")
print("Found:", p["found"])
if p["found"]:
    for rec in p["records"]:
        print("  Sheet:", rec["sheet"])
        print("  Customer:", rec["customer"])
        print("  Qty:", rec["quantity"])
        print("  Statuses:", rec["department_statuses"])
