"""
bom_loader.py — Combination-Aware BOM Intelligence Engine for Unilights.
Parses all 55+ BOM Excel files, including multi-sheet 'Product Family' files
that encode 50+ SKU combinations via a Backend data attribute mapping table.

ARCHITECTURE
============
Every BOM file falls into one of two categories:

A) SIMPLE — Single recipe sheet.
   └── 'Stock Item': one list of components → ONE product in the database.

B) ADVANCED (Product Family) — Multi-sheet file with:
   ├── 'Stock Item'   : Base/common components shared by ALL variants.
   ├── 'Backend data' : Attribute lookup table.
   │                    7 columns (TRIM, HOUSING, REFLECTOR, BEAM ANGLE,
   │                    COLOR TEMP, DRIVING SYSTEM, PCB).
   │                    Each column has rows of {Code → Item Name} mappings.
   └── '<MODEL>-SKU'  : Full list of every SKU with its attribute choices.
       Columns: SKU Code, Product Name, Trim, Beam Angle,
                Color Temp, Driving System, Watt …

DATABASE SCHEMA (normalized, one row per component per SKU)
===========================================================
    product_name   : exact model/SKU name (e.g. 'SRDR12F30T')
    sku_code       : same as product_name when from SKU sheet
    item_name      : component / material name
    category       : attribute category (TRIM, DRIVING SYSTEM …)
                     OR 'BASE' for common Stock-Item components
    is_variable    : True if the component changes across SKU variants
    quantity       : qty required per unit
    rate           : unit price (INR) — Col L
    cost_inr       : INR cost = rate × qty — Col M (PRIMARY for totals)
    usd            : imported price in USD — Col N
    ins_freight    : insurance + freight — Col O
    bcd            : basic customs duty — Col P
    total_cost_usd : USD contribution — Col Q (secondary, NOT for INR totals)
    source_file    : source Excel filename
"""

import os
import re
import pandas as pd

from ..config import BOM_DIR

# ── Attribute column groups in the Backend data lookup table ─────────────────
_ATTRIBUTE_GROUPS = [
    "TRIM", "HOUSING/HS", "REFLECTOR",
    "BEAM ANGLE", "COLOUR TEMPERATURE", "DRIVING SYSTEM", "PCB",
    # Alternate spellings:
    "COLOR TEMP", "COLOUR TEMP",
]

# ── Column name aliases for the Stock Item component list ────────────────────
_COL_ALIASES = {
    "item_name":      ["bom component - item name", "item name", "component name"],
    "item_type":      ["bom component - type of item", "type of item", "type"],
    "godown":         ["bom component - godown", "bom component - location",
                       "godown", "warehouse", "store", "location"],
    "quantity":       ["bom component - quantity", "quantity", "qty"],
    "rate":           ["unit price", "rate", "unit cost"],     # Col L
    "cost_inr":       ["cost"],                                # Col M  ← PRIMARY
    "usd":            ["usd"],
    "ins_freight":    ["ins&fred", "ins & fred", "ins&freight", "insurance"],
    "bcd":            ["bcd"],
    "total_cost_usd": ["total cost", "total"],                 # Col Q  ← secondary
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _clean_product_name(filename: str) -> str:
    """Extract clean model name from filename."""
    name = filename.replace(".xlsx", "").replace(".xls", "")
    name = re.sub(r"\s*-?\s*BOM\s*", "", name, flags=re.IGNORECASE)
    return name.strip(" -_")


def _find_col(columns: list, candidates: list) -> str | None:
    """Return matching column from list, case-insensitive."""
    cols_lower = {c.strip().lower(): c for c in columns}
    for cand in candidates:
        if cand.strip().lower() in cols_lower:
            return cols_lower[cand.strip().lower()]
    return None


def _detect_header_row(df_raw: pd.DataFrame) -> int:
    """Find the row index containing actual column headers."""
    signals = ["item name", "quantity", "rate", "cost", "type", "godown",
               "bom component", "unit price"]
    for i, row in df_raw.iterrows():
        row_str = " ".join(str(v).lower().strip()
                           for v in row.values if pd.notna(v))
        if sum(1 for s in signals if s in row_str) >= 2:
            return i
    return 0


def _safe_float(val) -> float | None:
    """Convert to float; return None if not possible."""
    try:
        v = float(val)
        return v if pd.notna(v) else None
    except (TypeError, ValueError):
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# STOCK ITEM SHEET PARSER  (shared for both Simple and Advanced files)
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_stock_item_sheet(fpath: str, product_name: str) -> list[dict]:
    """
    Parse the 'Stock Item' sheet of a BOM file.
    Returns a list of component dicts (base/common materials).
    """
    records = []
    try:
        df_raw = pd.read_excel(fpath, sheet_name="Stock Item", header=None)
        header_row = _detect_header_row(df_raw)
        df = pd.read_excel(fpath, sheet_name="Stock Item", header=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").dropna(how="all", axis=1)

        col_map = {}
        for key, aliases in _COL_ALIASES.items():
            found = _find_col(list(df.columns), aliases)
            if found is None:
                for c in df.columns:
                    if any(a in c.lower() for a in aliases):
                        found = c
                        break
            col_map[key] = found

        if col_map["item_name"] is None:
            return records

        for _, row in df.iterrows():
            item = str(row.get(col_map["item_name"], "")).strip()
            if not item or item.lower() in ["nan", "", "name", "item name",
                                             "bom component - item name"]:
                continue
            if any(x in item.lower() for x in ["total", "sub total", "subtotal"]):
                continue

            qty  = _safe_float(row.get(col_map["quantity"]) if col_map["quantity"] else None)
            rate = _safe_float(row.get(col_map["rate"]) if col_map["rate"] else None)
            cost = _safe_float(row.get(col_map["cost_inr"]) if col_map["cost_inr"] else None)

            if (cost is None or cost == 0) and rate and qty:
                cost = rate * qty

            records.append({
                "product_name":   product_name,
                "sku_code":       product_name,
                "item_name":      item,
                "category":       "BASE",
                "is_variable":    False,
                "item_type":      str(row.get(col_map["item_type"], "")).strip()
                                  if col_map["item_type"] else "",
                "godown":         str(row.get(col_map["godown"], "")).strip()
                                  if col_map["godown"] else "",
                "quantity":       qty,
                "rate":           rate,
                "cost_inr":       cost,
                "usd":            _safe_float(row.get(col_map["usd"]) if col_map["usd"] else None),
                "ins_freight":    _safe_float(row.get(col_map["ins_freight"]) if col_map["ins_freight"] else None),
                "bcd":            _safe_float(row.get(col_map["bcd"]) if col_map["bcd"] else None),
                "total_cost_usd": _safe_float(row.get(col_map["total_cost_usd"]) if col_map["total_cost_usd"] else None),
                "source_file":    os.path.basename(fpath),
            })
    except Exception as e:
        print(f"[bom_loader] Stock Item parse error in {os.path.basename(fpath)}: {e}")

    return records


# ═══════════════════════════════════════════════════════════════════════════════
# BACKEND DATA SHEET PARSER  (attribute lookup table)
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_backend_attribute_table(fpath: str) -> dict:
    """
    Parse the 'Backend data' sheet to extract the attribute lookup table.
    Returns:
        {
          'TRIM':            {'R': {'item': '...', 'rate': 7.0, 'qty': 1.0}, ...},
          'DRIVING SYSTEM':  {'12T-': {'item': 'PS 12W 300mA ...', 'rate': None}, ...},
          ...
        }
    """
    attribute_table = {}

    try:
        df = pd.read_excel(fpath, sheet_name="Backend data", header=None)

        attr_header_row = None
        for i, row in df.iterrows():
            vals = [str(v).strip().upper() for v in row if pd.notna(v)]
            if "TRIM" in vals and (
                "HOUSING/HS" in vals or "COLOUR TEMPERATURE" in vals or
                "DRIVING SYSTEM" in vals or "COLOR TEMP" in vals
            ):
                attr_header_row = i
                break

        if attr_header_row is None:
            return attribute_table

        header_row = df.iloc[attr_header_row]
        col_to_group: dict[int, str] = {}
        canonical = {
            "TRIM": "TRIM",
            "HOUSING/HS": "HOUSING",
            "REFLECTOR": "REFLECTOR",
            "BEAM ANGLE": "BEAM_ANGLE",
            "COLOUR TEMPERATURE": "COLOR_TEMP",
            "COLOR TEMP": "COLOR_TEMP",
            "DRIVING SYSTEM": "DRIVING_SYSTEM",
            "PCB": "PCB",
        }
        for col_idx, val in header_row.items():
            v = str(val).strip().upper()
            if v in canonical:
                col_to_group[col_idx] = canonical[v]

        if not col_to_group:
            return attribute_table

        for grp in col_to_group.values():
            attribute_table[grp] = {}

        sub_header_row = attr_header_row + 1
        sub = df.iloc[sub_header_row]

        group_cols: dict[str, dict] = {}
        sorted_group_cols = sorted(col_to_group.items())
        for i, (start_col, grp) in enumerate(sorted_group_cols):
            next_start = sorted_group_cols[i + 1][0] if i + 1 < len(sorted_group_cols) else start_col + 10
            roles = {}
            for col_idx in range(start_col, next_start):
                cell = str(sub.get(col_idx, "")).strip().lower()
                if "code" in cell:
                    roles["code"] = col_idx
                elif "item name" in cell:
                    roles["item_name"] = col_idx
                elif "quantity" in cell or "qty" in cell:
                    roles["quantity"] = col_idx
                elif "cost" in cell:
                    roles["cost"] = col_idx
            group_cols[grp] = roles

        for row_i in range(sub_header_row + 1, len(df)):
            row = df.iloc[row_i]
            for grp, roles in group_cols.items():
                code_col = roles.get("code")
                name_col = roles.get("item_name")
                qty_col  = roles.get("quantity")
                cost_col = roles.get("cost")

                code = str(row.get(code_col, "")).strip() if code_col is not None else ""
                name = str(row.get(name_col, "")).strip() if name_col is not None else ""
                qty  = _safe_float(row.get(qty_col)) if qty_col is not None else None
                cost = _safe_float(row.get(cost_col)) if cost_col is not None else None

                if code and code.lower() not in ["nan", "", "code"]:
                    attribute_table[grp][code] = {
                        "item": name if name and name.lower() != "nan" else None,
                        "quantity": qty or 1.0,
                        "cost": cost,
                    }

    except Exception as e:
        print(f"[bom_loader] Backend data parse error in {os.path.basename(fpath)}: {e}")

    return attribute_table


# ═══════════════════════════════════════════════════════════════════════════════
# SKU SHEET PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_sku_sheet(fpath: str, sheet_name: str) -> pd.DataFrame | None:
    """
    Parse the SKU combinations sheet.
    Returns a DataFrame with normalised columns.
    """
    try:
        df = pd.read_excel(fpath, sheet_name=sheet_name)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        rename_map = {
            "sku_code":       "sku_code",
            "product_name":   "product_name",
            "selling_price":  "selling_price",
            "trim":           "trim",
            "beam_angle":     "beam_angle",
            "color_temp":     "color_temp",
            "colour_temp":    "color_temp",
            "driving_system": "driving_system",
            "watt":           "watt",
        }
        df = df.rename(columns=rename_map)
        if "sku_code" in df.columns:
            df = df[df["sku_code"].notna()].copy()
        return df
    except Exception as e:
        print(f"[bom_loader] SKU sheet parse error ({sheet_name}): {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# FILE TYPE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_file_type(fpath: str) -> tuple[str, list[str]]:
    """Returns ('simple', []) or ('advanced', [sku_sheet_names])."""
    try:
        sheets = pd.ExcelFile(fpath).sheet_names
        has_backend = "Backend data" in sheets
        sku_sheets = [s for s in sheets if "SKU" in s.upper()]
        if has_backend and sku_sheets:
            return "advanced", sku_sheets
        return "simple", []
    except Exception:
        return "simple", []


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED FILE HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

def _load_advanced_file(fpath: str, sku_sheets: list[str]) -> list[dict]:
    """Load an advanced (Product Family) BOM file into normalised records."""
    records_out = []
    product_family = _clean_product_name(os.path.basename(fpath))

    base_records = _parse_stock_item_sheet(fpath, product_family)
    attr_table   = _parse_backend_attribute_table(fpath)

    for sku_sheet in sku_sheets:
        sku_df = _parse_sku_sheet(fpath, sku_sheet)
        if sku_df is None or sku_df.empty:
            continue

        for _, sku_row in sku_df.iterrows():
            sku_code = str(sku_row.get("sku_code", "")).strip()
            if not sku_code or sku_code.lower() == "nan":
                continue

            product_name = str(sku_row.get("product_name", sku_code)).strip()

            for base in base_records:
                rec = base.copy()
                rec["product_name"] = product_name
                rec["sku_code"]     = sku_code
                rec["is_variable"]  = False
                records_out.append(rec)

            sku_attr_map = {
                "TRIM":           str(sku_row.get("trim", "")).strip(),
                "BEAM_ANGLE":     str(sku_row.get("beam_angle", "")).strip(),
                "COLOR_TEMP":     str(sku_row.get("color_temp", "")).strip(),
                "DRIVING_SYSTEM": str(sku_row.get("driving_system", "")).strip(),
            }

            for attr_group, attr_value in sku_attr_map.items():
                if not attr_value or attr_value.lower() == "nan":
                    continue
                if attr_group not in attr_table:
                    continue
                matched_entry = None
                for code, entry in attr_table[attr_group].items():
                    item_lower = (entry.get("item") or "").lower()
                    if item_lower and attr_value.lower() in item_lower:
                        matched_entry = entry
                        break

                if matched_entry and matched_entry.get("item"):
                    cost = matched_entry.get("cost")
                    qty  = matched_entry.get("quantity", 1.0)
                    rate = (cost / qty) if cost and qty else None
                    records_out.append({
                        "product_name":   product_name,
                        "sku_code":       sku_code,
                        "item_name":      matched_entry["item"],
                        "category":       attr_group,
                        "is_variable":    True,
                        "item_type":      attr_group.replace("_", " ").title(),
                        "godown":         "",
                        "quantity":       qty,
                        "rate":           rate,
                        "cost_inr":       cost,
                        "usd":            None,
                        "ins_freight":    None,
                        "bcd":            None,
                        "total_cost_usd": None,
                        "source_file":    os.path.basename(fpath),
                    })

    return records_out


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def load_bom_database(bom_dir: str | None = None) -> pd.DataFrame:
    """Load and normalize all BOM Excel files into a single master DataFrame."""
    if bom_dir is None:
        bom_dir = str(BOM_DIR)

    files = [f for f in os.listdir(bom_dir) if f.endswith(".xlsx")]
    all_records: list[dict] = []
    simple_count = advanced_count = skipped_count = 0

    for fname in sorted(files):
        fpath = os.path.join(bom_dir, fname)
        file_type, sku_sheets = _detect_file_type(fpath)
        try:
            if file_type == "advanced":
                recs = _load_advanced_file(fpath, sku_sheets)
                all_records.extend(recs)
                advanced_count += 1
            else:
                product_name = _clean_product_name(fname)
                recs = _parse_stock_item_sheet(fpath, product_name)
                if recs:
                    all_records.extend(recs)
                    simple_count += 1
                else:
                    skipped_count += 1
        except Exception as e:
            print(f"[bom_loader] ERROR on {fname}: {e}")
            skipped_count += 1

    master_df = pd.DataFrame(all_records)
    total = simple_count + advanced_count
    print(
        f"[bom_loader] Loaded {len(master_df)} rows from {total}/{len(files)} files "
        f"({simple_count} simple, {advanced_count} advanced/family, {skipped_count} skipped)."
    )
    if master_df.empty:
        return master_df

    for col in ["quantity", "rate", "cost_inr", "usd", "ins_freight", "bcd", "total_cost_usd"]:
        if col in master_df.columns:
            master_df[col] = pd.to_numeric(master_df[col], errors="coerce")

    return master_df


# ── Singleton ─────────────────────────────────────────────────────────────────
_BOM_DB: pd.DataFrame | None = None


def get_bom_db() -> pd.DataFrame:
    global _BOM_DB
    if _BOM_DB is None:
        _BOM_DB = load_bom_database()
    return _BOM_DB
