"""Inspecciona la estructura del XLSX dentro del ZIP."""
import zipfile, sys, io
from pathlib import Path
import pandas as pd

raw = Path("data/raw")
target = sys.argv[1] if len(sys.argv) > 1 else "PROV_02_202307_1.zip"

with zipfile.ZipFile(raw / target) as arch:
    xlsx_name = [f for f in arch.namelist() if f.endswith(".xlsx")][0]
    print(f"Fichero dentro del ZIP: {xlsx_name}\n")
    data = arch.read(xlsx_name)

xl = pd.ExcelFile(io.BytesIO(data))
print(f"Hojas: {xl.sheet_names}\n")

for sheet in xl.sheet_names:
    df = xl.parse(sheet, header=None, nrows=6)
    print(f"=== Hoja: {sheet!r} ===")
    print(df.to_string())
    print()
