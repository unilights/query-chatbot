import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tools import get_all_orders_by_customer, get_product_summary

print("=== SEARCH TEST: J.R. Electro ===")
r1 = get_all_orders_by_customer("J.R. Electro")
print(f"Found: {r1['found']}")
if r1['found']:
    print(f"Total orders: {r1['total']}")
    print(f"First 2: {r1['orders'][:2]}")

print("\n=== PRODUCT TEST: GLWR18W 35K ===")
r2 = get_product_summary("GLWR18W 35K")
print(f"Found: {r2['found']}")
if r2['found']:
    for rec in r2['records']:
        print(f"  Sheet: {rec['sheet']} | Customer: {rec['customer']}")
