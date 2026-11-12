from pathlib import Path
from openpyxl import load_workbook

from extract_pilot_data import RELEASES

for release_year, metric_year, path in RELEASES:
    wb = load_workbook(path, read_only=True, data_only=True)
    print(f"\n{release_year}: {path.name}")
    print("sheets:", wb.sheetnames)
    sheet_name = "Data" if "Data" in wb.sheetnames else "Career"
    ws = wb[sheet_name]
    headers = [str(value) if value is not None else "" for value in next(ws.iter_rows(values_only=True))]
    print("rows:", ws.max_row - 1, "columns:", len(headers))
    print("headers:", " | ".join(headers))
    wb.close()
