import json
with open('columns_info.json', 'r') as f:
    d = json.load(f)

cols = set()
for sheet_dict in d.values():
    if isinstance(sheet_dict, dict):
        for columns in sheet_dict.values():
            if isinstance(columns, list):
                for c in columns:
                    c = str(c).strip()
                    if c and not c.startswith('Unnamed'):
                        cols.add(c)

with open('unique_cols.txt', 'w') as f:
    f.write('\n'.join(sorted(list(cols))))
