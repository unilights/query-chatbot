import pandas as pd
import warnings
from pathlib import Path
warnings.filterwarnings('ignore')

product = 'TTLB24W 35K'
results = []

# Check PENDING SHEET 2 - Hold Orders
df1 = pd.read_excel(r'data\orders\PENDING SHEET 2.xlsx', sheet_name='Hold Orders')
match1 = df1[df1.apply(lambda row: row.astype(str).str.contains(product, case=False).any(), axis=1)]
results.append('=== PENDING SHEET 2 - Hold Orders ===')
results.append(match1.to_string() if not match1.empty else 'Not found')

# Check Customization Orders
df2 = pd.read_excel(r'data\orders\Customization Orders FY 22-23.xlsx', sheet_name='Sheet1')
match2 = df2[df2.apply(lambda row: row.astype(str).str.contains(product, case=False).any(), axis=1)]
results.append('\n=== Customization Orders - Sheet1 ===')
results.append(match2.to_string() if not match2.empty else 'Not found')

# Check all sheets in Billing Sheet
xl = pd.ExcelFile(r'data\orders\Billing Sheet.xlsx')
for sname in xl.sheet_names:
    df3 = pd.read_excel(r'data\orders\Billing Sheet.xlsx', sheet_name=sname)
    match3 = df3[df3.apply(lambda row: row.astype(str).str.contains(product, case=False).any(), axis=1)]
    if not match3.empty:
        results.append(f'\n=== Billing Sheet - {sname} ===')
        results.append(match3.to_string())

with open(Path(__file__).parent / "output" / "ttlb_search.txt", 'w') as f:
    f.write('\n'.join(results))
print('Done')
