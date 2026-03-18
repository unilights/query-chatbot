import pandas as pd
import os
import json

directory = r"d:\unilights\sales-approval-process"
files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]

results = {}

for f in files:
    file_path = os.path.join(directory, f)
    try:
        xls = pd.ExcelFile(file_path)
        file_results = {}
        for sheet_name in xls.sheet_names:
            try:
                # Read just the first row to get columns
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=2)
                file_results[sheet_name] = [str(col) for col in df.columns]
            except Exception as e:
                file_results[sheet_name] = f"Error: {e}"
        results[f] = file_results
    except Exception as e:
        results[f] = f"Error: {e}"

output_path = os.path.join(directory, 'columns_info.json')
with open(output_path, 'w', encoding='utf-8') as out:
    json.dump(results, out, indent=4)

print("Extraction complete. Check columns_info.json")
