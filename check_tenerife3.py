import sys, zipfile, io
import pandas as pd
sys.path.insert(0, '.')

z = zipfile.ZipFile('data/raw/PROV_02_202307_1.zip')
with z.open('PROV_02_202307_1.xlsx') as f:
    raw = pd.read_excel(io.BytesIO(f.read()), header=None)

# Buscar fila de Santa Cruz de Tenerife (cod 38)
# El codigo de provincia suele estar en alguna columna de las primeras
# Buscar filas donde aparezca "38" como codigo
for i, row in raw.iterrows():
    vals = row.tolist()
    if 38 in vals or '38' in [str(v) for v in vals]:
        # Ver si hay VOX en alguna columna
        row_str = ' | '.join(str(v) for v in vals if str(v) != 'nan')
        if 'VOX' in row_str or '38' in row_str:
            print(f"Fila {i}: {row_str[:200]}")
        if i > 5:
            break

# Buscar la cabecera para localizar columnas
print("\n--- Primeras 5 filas (cabecera) ---")
for i in range(5):
    print(f"Fila {i}:", [str(v) for v in raw.iloc[i].tolist() if str(v) != 'nan'][:20])

# Buscar columna VOX
header_row = None
for i in range(10):
    if any('VOX' in str(v) for v in raw.iloc[i].tolist()):
        header_row = i
        break
if header_row is not None:
    print(f"\nVOX encontrado en fila de cabecera {header_row}")
    cols = raw.iloc[header_row].tolist()
    vox_col = next(j for j, v in enumerate(cols) if 'VOX' in str(v))
    print(f"VOX en columna {vox_col}")
    # Buscar fila de Santa Cruz
    for i in range(header_row+1, len(raw)):
        row = raw.iloc[i]
        if str(row.iloc[3]) == '38' or row.iloc[3] == 38:
            print(f"\nSanta Cruz de Tenerife (fila {i}): VOX votos = {row.iloc[vox_col]}")
            break
