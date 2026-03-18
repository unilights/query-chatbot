"""
order_loader.py — Loads all order/billing Excel files into Pandas DataFrames.
"""
import os
import pandas as pd


def load_all_data(directory: str) -> dict[str, pd.DataFrame]:
    """
    Load every .xlsx file in *directory*.
    Returns a dict keyed by "{filename} - {sheet_name}" → DataFrame.
    """
    files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]
    all_dfs: dict[str, pd.DataFrame] = {}

    for file in files:
        file_path = os.path.join(directory, file)
        try:
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                # Drop fully-empty columns and rows
                df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                # Uniform column names: strip + uppercase
                df.columns = [str(c).strip().upper() for c in df.columns]
                # Forward-fill grouped customer/client headers
                cust_cols = [c for c in df.columns if any(x in c for x in ["CUSTOMER", "CLIENT"])]
                if cust_cols:
                    df[cust_cols] = df[cust_cols].ffill()
                all_dfs[f"{file} - {sheet_name}"] = df
        except Exception as e:
            print(f"[order_loader] Failed to load {file}: {e}")

    return all_dfs


def get_data_schema(dataframes: dict[str, pd.DataFrame]) -> dict:
    """Return column names and row counts for each loaded sheet."""
    return {
        name: {"columns": list(df.columns), "row_count": len(df)}
        for name, df in dataframes.items()
    }
