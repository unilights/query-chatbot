"""
config.py — Central configuration for paths, constants, and model settings.
All other modules import from here instead of hardcoding values.
"""
from pathlib import Path

# ── Project root (one level above this file: query-chatbot/) ──────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent

# ── Data directories ──────────────────────────────────────────────────────────
DATA_DIR = ROOT_DIR / "data" / "orders"   # Order & billing Excel files
BOM_DIR  = ROOT_DIR / "data" / "bom"      # Bill of Materials Excel files

# ── Anthropic / LLM settings ──────────────────────────────────────────────────
LLM_MODEL  = "claude-haiku-4-5-20251001"
MAX_TOKENS = 4096
