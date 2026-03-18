"""
declarations.py — Claude tool declarations and registry for the agent.
Add new tools here as the project grows.
"""
from typing import Any

from ..tools import (
    get_product_summary,
    get_all_orders_by_customer,
    get_stock_by_department,
    get_hold_orders,
    get_pending_dispatch,
    get_delivery_status,
    get_all_products_list,
    get_orders_summary,
    get_product_bom,
    calculate_batch_materials,
    compare_product_variants,
    find_products_by_material,
)

# ── Tool schema declarations (sent to Claude) ─────────────────────────────────
TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "get_product_summary",
        "description": "Get the full details and production status of a specific product or model number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_no": {"type": "string", "description": "The product model number or name, e.g. 'TTLB24W 35K'"}
            },
            "required": ["model_no"]
        }
    },
    {
        "name": "get_all_orders_by_customer",
        "description": "Get all orders placed by a specific customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "The customer or client name, e.g. 'J.R. Electro'"}
            },
            "required": ["customer_name"]
        }
    },
    {
        "name": "get_stock_by_department",
        "description": "Get all items with a positive/ready status in a specific production department or store.",
        "input_schema": {
            "type": "object",
            "properties": {
                "department_name": {
                    "type": "string",
                    "description": "The department column name. One of: 'mech store', 'electronic store', 'smd dep. kiran sir', 'th dep. madhavi madam', 'mech. production dep.', 'packing & burning monu'"
                },
                "model_no": {
                    "type": "string",
                    "description": "Optional product model number to filter the stock check.",
                }
            },
            "required": ["department_name"]
        }
    },
    {
        "name": "get_hold_orders",
        "description": "Get a list of all orders that are currently on hold.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_pending_dispatch",
        "description": "Get all items that are packed and ready for dispatch but not yet dispatched.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_delivery_status",
        "description": "Check if a specific product is ready to dispatch or still in production, and get its ETA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_no": {"type": "string", "description": "The product model number to check delivery status for."}
            },
            "required": ["model_no"]
        }
    },
    {
        "name": "get_all_products_list",
        "description": "Get a complete list of all product and model names across all data files.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_orders_summary",
        "description": "Get a high-level dashboard summary: total data rows, hold orders count, dispatch-ready count.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_product_bom",
        "description": "Get the full Bill of Materials (BOM) for a product: components, quantities, unit costs, and total manufacturing cost.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_name": {"type": "string", "description": "Product model name, e.g. 'SRDR12W-COB' or 'SBDR-24W'"}
            },
            "required": ["model_name"]
        }
    },
    {
        "name": "calculate_batch_materials",
        "description": "Calculate total raw materials and cost needed to produce multiple products in given quantities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "orders": {
                    "type": "array",
                    "description": "List of orders, e.g. [{\"model\": \"SRDR12W-COB\", \"quantity\": 500}]",
                    "items": {"type": "object"}
                }
            },
            "required": ["orders"]
        }
    },
    {
        "name": "compare_product_variants",
        "description": "Compare the Bill of Materials of two product models.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_a": {"type": "string", "description": "First product model name"},
                "model_b": {"type": "string", "description": "Second product model name"}
            },
            "required": ["model_a", "model_b"]
        }
    },
    {
        "name": "find_products_by_material",
        "description": "Find all products that use a specific component or material.",
        "input_schema": {
            "type": "object",
            "properties": {
                "material_name": {"type": "string", "description": "Material or component name to search for"}
            },
            "required": ["material_name"]
        }
    },
]

# ── Tool registry (name → callable) ──────────────────────────────────────────
TOOL_REGISTRY: dict[str, Any] = {
    "get_product_summary":       get_product_summary,
    "get_all_orders_by_customer": get_all_orders_by_customer,
    "get_stock_by_department":   get_stock_by_department,
    "get_hold_orders":           get_hold_orders,
    "get_pending_dispatch":      get_pending_dispatch,
    "get_delivery_status":       get_delivery_status,
    "get_all_products_list":     get_all_products_list,
    "get_orders_summary":        get_orders_summary,
    "get_product_bom":           get_product_bom,
    "calculate_batch_materials": calculate_batch_materials,
    "compare_product_variants":  compare_product_variants,
    "find_products_by_material": find_products_by_material,
}
