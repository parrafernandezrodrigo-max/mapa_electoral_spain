"""Muestra las primeras 10 filas de cualquier XLSX para detectar dónde están las cabeceras."""
from parser import _load_raw

for conv_id in ["202307", "201111", "201904"]:
    raw = _load_raw(conv_id)
    print(f"\n{'='*60}")
    print(f"{conv_id}  shape={raw.shape}")
    for i in range(8):
        row_vals = [str(raw.iloc[i, j] or "")[:25] for j in range(min(20, raw.shape[1]))]
        non_nan = sum(1 for v in row_vals if v and v != "nan" and v != "None")
        print(f"  fila {i} ({non_nan} no-vacíos): {row_vals[:6]}  …")
