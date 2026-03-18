"""
order_tools.py — Tools 1–8: Order, inventory, and dispatch query functions.
"""
from typing import Optional

from .helpers import _get_dfs, _normalize, _find_col, _status_is_positive, _fuzzy_compare

# ── Shared column name lists ──────────────────────────────────────────────────
_MODEL_COLS  = ["model no.", "model name", "product", "model no", "model_no"]
_CUST_COLS   = ["customer name", "client name"]
_QTY_COLS    = ["qty.", "qty", "quantity"]
_DEPT_COLS   = [
    "mech store", "electronic store", "smd dep. kiran sir",
    "th dep. madhavi madam", "mech. production dep.", "packing & burning monu",
]


# ── Tool 1 ────────────────────────────────────────────────────────────────────
def get_product_summary(model_no: str) -> dict:
    """Return a full summary for a given model number searched across all sheets."""
    results = []
    for sheet_name, raw_df in _get_dfs().items():
        df = _normalize(raw_df)
        model_col = _find_col(df, _MODEL_COLS)
        if model_col is None:
            continue

        matches = df[df[model_col].astype(str).apply(lambda x: _fuzzy_compare(x, model_no))]
        if matches.empty:
            continue

        for _, row in matches.iterrows():
            entry = {
                "sheet":                 sheet_name,
                "model_no":              str(row.get(model_col, "N/A")).strip(),
                "customer":              str(row.get(_find_col(df, _CUST_COLS) or "", "N/A")).strip(),
                "order_date_po":         str(row.get(_find_col(df, ["order date & po", "order date"]) or "", "N/A")).strip(),
                "quantity":              str(row.get(_find_col(df, _QTY_COLS) or "", "N/A")).strip(),
                "dispatch_plan_date":    str(row.get(_find_col(df, ["dispacth plan date", "dispatch plan date"]) or "", "N/A")).strip(),
                "dispatch_revised_date": str(row.get(_find_col(df, ["dispatch revised date"]) or "", "N/A")).strip(),
                "remarks":               str(row.get(_find_col(df, ["fg remarks", "remarks", "remark"]) or "", "N/A")).strip(),
                "problems":              str(row.get(_find_col(df, ["problems"]) or "", "N/A")).strip(),
                "department_statuses":   {},
            }
            for dept in _DEPT_COLS:
                col = _find_col(df, [dept])
                if col:
                    entry["department_statuses"][dept] = str(row.get(col, "N/A")).strip()
            results.append(entry)

    if not results:
        return {"found": False, "message": f"No records found for model: '{model_no}'"}
    return {"found": True, "records": results}


# ── Tool 2 ────────────────────────────────────────────────────────────────────
def get_all_orders_by_customer(customer_name: str) -> dict:
    """Return all orders across all sheets for a given customer name."""
    results = []
    for sheet_name, raw_df in _get_dfs().items():
        df = _normalize(raw_df)
        cust_col = _find_col(df, _CUST_COLS)
        if cust_col is None:
            continue

        matches = df[df[cust_col].astype(str).apply(lambda x: _fuzzy_compare(x, customer_name))]
        for _, row in matches.iterrows():
            results.append({
                "sheet":        sheet_name,
                "customer":     str(row.get(cust_col, "N/A")),
                "model":        str(row.get(_find_col(df, _MODEL_COLS) or "", "N/A")).strip(),
                "quantity":     str(row.get(_find_col(df, _QTY_COLS) or "", "N/A")).strip(),
                "order_date_po":str(row.get(_find_col(df, ["order date & po", "order date"]) or "", "N/A")).strip(),
                "remarks":      str(row.get(_find_col(df, ["fg remarks", "remarks", "remark"]) or "", "N/A")).strip(),
            })

    if not results:
        return {"found": False, "message": f"No orders found for customer: '{customer_name}'"}
    return {"found": True, "total": len(results), "orders": results}


# ── Tool 3 ────────────────────────────────────────────────────────────────────
def get_stock_by_department(department_name: str, model_no: Optional[str] = None) -> dict:
    """
    Return all items where the given department status is positive.
    Optionally filter by model_no.
    """
    results = []
    for sheet_name, raw_df in _get_dfs().items():
        df = _normalize(raw_df)
        dept_col = _find_col(df, [department_name])
        if dept_col is None:
            continue
        model_col = _find_col(df, _MODEL_COLS)
        qty_col   = _find_col(df, _QTY_COLS)

        for _, row in df.iterrows():
            current_model = str(row.get(model_col, "N/A") if model_col else "N/A").strip()
            if model_no and not _fuzzy_compare(current_model, model_no):
                continue
            if _status_is_positive(str(row.get(dept_col, ""))):
                results.append({
                    "model":    current_model,
                    "quantity": str(row.get(qty_col, "N/A") if qty_col else "N/A").strip(),
                    "status":   str(row.get(dept_col, "")).strip(),
                    "sheet":    sheet_name,
                })

    total_qty = 0
    for r in results:
        try:
            total_qty += int(float(r["quantity"]))
        except (ValueError, TypeError):
            pass

    if not results:
        msg = f"No items with a positive status found in department: '{department_name}'"
        if model_no:
            msg += f" for model: '{model_no}'"
        return {"found": False, "message": msg}
    return {"found": True, "department": department_name, "total_quantity": total_qty, "items": results}


# ── Tool 4 ────────────────────────────────────────────────────────────────────
def get_hold_orders() -> dict:
    """Return all orders currently on hold."""
    results = []
    for sheet_name, raw_df in _get_dfs().items():
        if "hold" not in sheet_name.lower():
            continue
        df = _normalize(raw_df)
        model_col = _find_col(df, _MODEL_COLS)
        cust_col  = _find_col(df, _CUST_COLS)
        qty_col   = _find_col(df, _QTY_COLS)

        for _, row in df.dropna(subset=[model_col] if model_col else df.columns[:1]).iterrows():
            results.append({
                "model":    str(row.get(model_col, "N/A") if model_col else "N/A").strip(),
                "customer": str(row.get(cust_col, "N/A") if cust_col else "N/A").strip(),
                "quantity": str(row.get(qty_col, "N/A") if qty_col else "N/A").strip(),
                "sheet":    sheet_name,
            })

    if not results:
        return {"found": False, "message": "No hold orders found."}
    return {"found": True, "total": len(results), "hold_orders": results}


# ── Tool 5 ────────────────────────────────────────────────────────────────────
def get_pending_dispatch() -> dict:
    """Return items that are packed and ready but not yet dispatched."""
    results = []
    for sheet_name, raw_df in _get_dfs().items():
        df = _normalize(raw_df)
        pack_col = _find_col(df, ["packing & burning monu"])
        if pack_col is None:
            continue
        model_col = _find_col(df, _MODEL_COLS)
        cust_col  = _find_col(df, _CUST_COLS)
        qty_col   = _find_col(df, _QTY_COLS)
        date_col  = _find_col(df, ["dispacth plan date", "dispatch plan date"])

        for _, row in df.iterrows():
            if _status_is_positive(str(row.get(pack_col, ""))):
                results.append({
                    "model":              str(row.get(model_col, "N/A") if model_col else "N/A").strip(),
                    "customer":           str(row.get(cust_col, "N/A") if cust_col else "N/A").strip(),
                    "quantity":           str(row.get(qty_col, "N/A") if qty_col else "N/A").strip(),
                    "dispatch_plan_date": str(row.get(date_col, "N/A") if date_col else "N/A").strip(),
                    "sheet":              sheet_name,
                })

    if not results:
        return {"found": False, "message": "No items are currently ready for dispatch."}
    return {"found": True, "total": len(results), "ready_items": results}


# ── Tool 6 ────────────────────────────────────────────────────────────────────
def get_delivery_status(model_no: str) -> dict:
    """Return the delivery/production pipeline status for a product."""
    summary = get_product_summary(model_no)
    if not summary["found"]:
        return {"found": False, "message": f"No delivery info found for: '{model_no}'"}

    responses = []
    for record in summary["records"]:
        statuses = record.get("department_statuses", {})
        is_ready = _status_is_positive(statuses.get("packing & burning monu", ""))

        if is_ready:
            current_stage = "Packed & Ready for Dispatch"
        else:
            current_stage = "In Progress — early production stage"
            for dept in reversed(_DEPT_COLS):
                if _status_is_positive(statuses.get(dept, "")):
                    current_stage = f"In Progress — cleared {dept}"
                    break

        responses.append({
            "model":                 record["model_no"],
            "customer":              record["customer"],
            "quantity":              record["quantity"],
            "current_stage":         current_stage,
            "is_ready_to_dispatch":  is_ready,
            "dispatch_plan_date":    record["dispatch_plan_date"],
            "dispatch_revised_date": record["dispatch_revised_date"],
            "remarks":               record["remarks"],
            "problems":              record["problems"],
            "source_sheet":          record["sheet"],
        })

    return {"found": True, "delivery_status": responses}


# ── Tool 7 ────────────────────────────────────────────────────────────────────
def get_all_products_list() -> dict:
    """Return a unique sorted list of all product/model names across all sheets."""
    products: set[str] = set()
    for _, raw_df in _get_dfs().items():
        df = _normalize(raw_df)
        col = _find_col(df, _MODEL_COLS)
        if col:
            vals = df[col].dropna().astype(str).str.strip()
            products.update(vals[vals.str.len() > 1].tolist())

    products.discard("nan")
    products.discard("N/A")
    sorted_products = sorted(products)
    return {"found": True, "total_products": len(sorted_products), "products": sorted_products}


# ── Tool 8 ────────────────────────────────────────────────────────────────────
def get_orders_summary() -> dict:
    """Return a high-level dashboard summary: rows loaded, hold count, dispatch-ready count."""
    dfs = _get_dfs()
    total_rows = 0
    hold_count = 0
    dispatch_ready = 0

    for sheet_name, raw_df in dfs.items():
        df = _normalize(raw_df)
        total_rows += len(df)

        if "hold" in sheet_name.lower():
            hold_count += len(df.dropna(how="all"))

        pack_col = _find_col(df, ["packing & burning monu"])
        if pack_col:
            dispatch_ready += df[df[pack_col].astype(str).apply(_status_is_positive)].shape[0]

    return {
        "found": True,
        "summary": {
            "total_sheets_loaded":    len(dfs),
            "total_data_rows":        total_rows,
            "hold_orders_count":      hold_count,
            "ready_to_dispatch_count": dispatch_ready,
            "sheets":                 list(dfs.keys()),
        }
    }
