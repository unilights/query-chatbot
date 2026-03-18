"""
helpers.py — Shared utilities used by order_tools and bom_tools.
"""
import re
import pandas as pd
from difflib import SequenceMatcher

from ..loaders.order_loader import load_all_data
from ..config import DATA_DIR

# ── Order DataFrame singleton ─────────────────────────────────────────────────
_dfs: dict[str, pd.DataFrame] | None = None


def _get_dfs() -> dict[str, pd.DataFrame]:
    global _dfs
    if _dfs is None:
        _dfs = load_all_data(str(DATA_DIR))
    return _dfs


# ── DataFrame utilities ───────────────────────────────────────────────────────

def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names, strip whitespace, drop fully-empty rows."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df.dropna(how="all")


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first column name (case-insensitive) that matches any candidate."""
    for c in df.columns:
        if c.strip().lower() in [x.lower() for x in candidates]:
            return c
    return None


# ── Status / matching helpers ─────────────────────────────────────────────────

def _status_is_positive(status: str) -> bool:
    """Return True if a department status string means the item is cleared/ready."""
    if not isinstance(status, str):
        return False
    status_lower = status.lower().strip()
    if any(k in status_lower for k in ["ok", "ready", "available", "done", "clear"]):
        return True
    digits = re.findall(r'\d+', status)
    if digits:
        try:
            if float(digits[0]) > 0:
                return True
        except ValueError:
            pass
    return False


def _fuzzy_compare(s1: str, s2: str) -> bool:
    """Compare two strings via substring check or SequenceMatcher (ratio > 0.8)."""
    clean1 = re.sub(r'[^a-zA-Z0-9]', '', str(s1)).lower()
    clean2 = re.sub(r'[^a-zA-Z0-9]', '', str(s2)).lower()
    if not clean1 or not clean2:
        return False
    if clean1 in clean2 or clean2 in clean1:
        return True
    return SequenceMatcher(None, clean1, clean2).ratio() > 0.8
