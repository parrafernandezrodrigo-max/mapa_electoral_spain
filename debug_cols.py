"""Ver los valores exactos en las filas de cabecera, columnas 14-25."""
from parser import _load_raw

for conv_id in ["202307", "201111"]:
    raw = _load_raw(conv_id)
    print(f"\n{'='*60}  {conv_id}")
    for fila in [3, 4, 5]:
        print(f"\n  --- fila {fila} ---")
        for col in range(14, 22):
            val = raw.iloc[fila, col]
            print(f"    col {col}: {val!r}  type={type(val).__name__}")
