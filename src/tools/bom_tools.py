"""
bom_tools.py — Tools 9–12: Bill of Materials query and analysis functions.
"""
import re
import pandas as pd
from difflib import get_close_matches, SequenceMatcher

from ..loaders.bom_loader import get_bom_db


# ── BOM-specific helpers ──────────────────────────────────────────────────────

def _bom_fuzzy_find(db: pd.DataFrame, model_name: str) -> pd.DataFrame:
    """Find BOM rows for a product using fuzzy matching on product_name."""
    clean = re.sub(r'[^a-zA-Z0-9]', '', model_name).lower()

    # Exact substring match first
    subset = db[
        db["product_name"]
        .str.replace(r'[^a-zA-Z0-9]', '', regex=True)
        .str.lower()
        .str.contains(clean, na=False)
    ]
    if not subset.empty:
        return subset

    # Fallback: difflib close matches
    all_products = db["product_name"].unique().tolist()
    cleaned_map = {re.sub(r'[^a-zA-Z0-9]', '', p).lower(): p for p in all_products}
    close = get_close_matches(clean, list(cleaned_map.keys()), n=3, cutoff=0.7)
    if close:
        matched = [cleaned_map[c] for c in close]
        return db[db["product_name"].isin(matched)]

    return db.iloc[0:0]  # empty


# ── Global material rate reference (singleton) ────────────────────────────────
_GLOBAL_MATERIAL_RATES: dict[str, dict] | None = None


def _get_global_material_reference() -> dict:
    """Build a global mapping of item_name → {'rate': float, 'source': str}."""
    global _GLOBAL_MATERIAL_RATES
    if _GLOBAL_MATERIAL_RATES is not None:
        return _GLOBAL_MATERIAL_RATES

    db = get_bom_db()
    valid = db[db["rate"] > 0].drop_duplicates(subset=["item_name"], keep="first")
    _GLOBAL_MATERIAL_RATES = {
        str(row["item_name"]): {"rate": float(row["rate"]), "source": str(row["product_name"])}
        for _, row in valid.iterrows()
    }
    return _GLOBAL_MATERIAL_RATES


# ── Tool 9 ────────────────────────────────────────────────────────────────────
def get_product_bom(model_name: str) -> dict:
    """Return the complete Bill of Materials for a product, with missing-rate fill-in."""
    db = get_bom_db()
    rows = _bom_fuzzy_find(db, model_name)

    if rows.empty:
        return {"found": False, "message": f"No BOM found for model: '{model_name}'. Check exact model name."}

    matched_product = rows["product_name"].iloc[0]
    rows = rows[rows["product_name"] == matched_product]
    global_rates = _get_global_material_reference()

    components = []
    total_cost = 0.0
    for _, row in rows.iterrows():
        item_name = str(row["item_name"])
        qty       = float(row["quantity"])  if pd.notna(row["quantity"])  else 0.0
        rate_val  = float(row["rate"])      if pd.notna(row["rate"])      and row["rate"]     > 0 else 0.0
        cost_val  = float(row["cost_inr"])  if pd.notna(row["cost_inr"]) and row["cost_inr"] > 0 else 0.0

        fetched_label = None
        if rate_val <= 0:
            ref = global_rates.get(item_name)
            if ref:
                rate_val      = ref["rate"]
                cost_val      = rate_val * qty
                fetched_label = f"Fetched from {ref['source']}"

        total_cost += cost_val
        components.append({
            "item":        item_name,
            "type":        str(row["item_type"]),
            "godown":      str(row["godown"]),
            "quantity":    qty,
            "rate_inr":    round(rate_val, 3) if rate_val > 0 else None,
            "cost_inr":    round(cost_val, 2),
            "fetched_from": fetched_label,
        })

    return {
        "found":                        True,
        "product":                      matched_product,
        "total_components":             len(components),
        "total_manufacturing_cost_inr": round(total_cost, 2),
        "components":                   components,
    }


# ── Tool 10 ───────────────────────────────────────────────────────────────────
def calculate_batch_materials(orders: list) -> dict:
    """
    Aggregate total materials and cost for a production batch.
    Input: [{"model": "SRDR12W-COB", "quantity": 500}, ...]
    """
    db = get_bom_db()
    aggregated: dict[str, dict] = {}
    grand_total = 0.0
    errors = []

    for order in orders:
        model    = order.get("model", "")
        batch_qty = float(order.get("quantity", 1))
        rows = _bom_fuzzy_find(db, model)

        if rows.empty:
            errors.append(f"No BOM found for: {model}")
            continue

        matched = rows["product_name"].iloc[0]
        rows = rows[rows["product_name"] == matched]

        for _, row in rows.iterrows():
            item         = str(row["item_name"])
            bom_qty      = float(row["quantity"])  if pd.notna(row["quantity"])  else 0.0
            unit_cost    = float(row["cost_inr"])  if pd.notna(row["cost_inr"]) else 0.0
            rate         = float(row["rate"])      if pd.notna(row["rate"])      else 0.0
            total_qty    = bom_qty * batch_qty
            total_cost   = (unit_cost / bom_qty * total_qty) if bom_qty else rate * total_qty

            if item in aggregated:
                aggregated[item]["total_quantity"] += total_qty
                aggregated[item]["total_cost"]     += total_cost
            else:
                aggregated[item] = {
                    "item":          item,
                    "total_quantity": total_qty,
                    "unit_rate_inr": rate,
                    "total_cost":    total_cost,
                }
            grand_total += total_cost

    return {
        "found":               True,
        "orders":              orders,
        "errors":              errors,
        "grand_total_cost_inr": round(grand_total, 2),
        "materials":           sorted(aggregated.values(), key=lambda x: -x["total_cost"]),
    }


# ── Tool 11 ───────────────────────────────────────────────────────────────────
def compare_product_variants(model_a: str, model_b: str) -> dict:
    """Compare the BOM of two product variants: differences, unique items, cost delta."""
    bom_a = get_product_bom(model_a)
    bom_b = get_product_bom(model_b)

    if not bom_a["found"]:
        return {"found": False, "message": f"BOM not found for: {model_a}"}
    if not bom_b["found"]:
        return {"found": False, "message": f"BOM not found for: {model_b}"}

    map_a = {c["item"]: c for c in bom_a["components"]}
    map_b = {c["item"]: c for c in bom_b["components"]}
    all_items = set(map_a) | set(map_b)

    differences = []
    only_in_a   = []
    only_in_b   = []

    for item in sorted(all_items):
        if item in map_a and item in map_b:
            qty_diff  = (map_b[item]["quantity"] or 0) - (map_a[item]["quantity"] or 0)
            cost_diff = (map_b[item]["cost_inr"] or 0) - (map_a[item]["cost_inr"] or 0)
            if abs(qty_diff) > 0.001 or abs(cost_diff) > 0.001:
                differences.append({
                    "item":                   item,
                    f"qty_{model_a}":         map_a[item]["quantity"],
                    f"qty_{model_b}":         map_b[item]["quantity"],
                    "qty_change":             round(qty_diff, 3),
                    "cost_change_inr":        round(cost_diff, 2),
                })
        elif item in map_a:
            only_in_a.append(item)
        else:
            only_in_b.append(item)

    return {
        "found":                 True,
        "product_a":             bom_a["product"],
        "product_b":             bom_b["product"],
        "cost_a_inr":            bom_a["total_manufacturing_cost_inr"],
        "cost_b_inr":            bom_b["total_manufacturing_cost_inr"],
        "cost_difference_inr":   round(bom_b["total_manufacturing_cost_inr"] - bom_a["total_manufacturing_cost_inr"], 2),
        "items_only_in_a":       only_in_a,
        "items_only_in_b":       only_in_b,
        "items_with_differences": differences,
    }


# ── Tool 12 ───────────────────────────────────────────────────────────────────
def find_products_by_material(material_name: str) -> dict:
    """Find all products that use a specific material or component."""
    db = get_bom_db()
    clean = re.sub(r'[^a-zA-Z0-9]', '', material_name).lower()

    def matches(item: str) -> bool:
        item_clean = re.sub(r'[^a-zA-Z0-9]', '', str(item)).lower()
        return clean in item_clean or SequenceMatcher(None, clean, item_clean).ratio() > 0.8

    hits = db[db["item_name"].apply(matches)]
    if hits.empty:
        return {"found": False, "message": f"No products found using material: '{material_name}'"}

    summary = (
        hits.groupby("product_name")
        .agg(quantity=("quantity", "first"), cost_inr=("cost_inr", "first"), item=("item_name", "first"))
        .reset_index()
        .to_dict("records")
    )
    return {
        "found":            True,
        "material_searched": material_name,
        "total_products":   len(summary),
        "products":         summary,
    }
